
import numpy as np

from movies.models import (
    MovieEmbedding,
    Review,
    Watchlist,
    WatchedMovie,
)

from .semantic_search import MODEL_NAME


def personalized_recommendations(user, limit=5):

    # Step 1: Retrieve positively rated movies
    liked_reviews = Review.objects.filter(
        user=user,
        rating__gte=7
    )

    # Step 2: Retrieve watchlisted movie IDs
    watchlisted_ids = set(
        Watchlist.objects.filter(user=user)
        .values_list("movie_id", flat=True)
    )

    # Step 3: Retrieve watched movie IDs
    watched_ids = set(
        WatchedMovie.objects.filter(user=user)
        .values_list("movie_id", flat=True)
    )

    # Step 4: Build preference weights
    preference_weights = {}

    for review in liked_reviews:
        preference_weights[review.movie_id] = (
            review.rating / 10
        )

    for movie_id in watchlisted_ids:
        preference_weights[movie_id] = max(
            preference_weights.get(movie_id, 0),
            0.7
        )

    # No positive preferences available
    if not preference_weights:
        return []

    # Step 5: Retrieve stored embeddings
    records = list(
        MovieEmbedding.objects
        .select_related("movie")
        .filter(model_name=MODEL_NAME)
        .order_by("movie_id")
    )

    # Exclude outdated or malformed embeddings
    records = [
        record for record in records
        if record.source_updated_at == record.movie.updated_at
        and isinstance(record.vector, list)
        and len(record.vector) == 384
    ]

    if not records:
        return []

    movies = [record.movie for record in records]

    embeddings = np.asarray(
        [record.vector for record in records],
        dtype=np.float32
    )

    # Step 6: Build the user's preference vector
    weighted_vectors = []
    weights = []

    for index, movie in enumerate(movies):
        if movie.id in preference_weights:
            weight = preference_weights[movie.id]

            weighted_vectors.append(
                embeddings[index] * weight
            )

            weights.append(weight)

    if not weighted_vectors:
        return []

    user_vector = np.sum(
        weighted_vectors,
        axis=0
    ) / sum(weights)

    # Normalize the preference vector
    norm = np.linalg.norm(user_vector)

    if not np.isfinite(norm) or norm == 0:
        return []

    user_vector = user_vector / norm

    # Step 7: Calculate similarity scores
    scores = np.dot(
        embeddings,
        user_vector
    )

    # Step 8: Exclude known movies
    rated_ids = set(
        Review.objects.filter(user=user)
        .values_list("movie_id", flat=True)
    )

    excluded_ids = (
        rated_ids | watched_ids | watchlisted_ids
    )

    results = []

    for index, movie in enumerate(movies):

        if movie.id in excluded_ids:
            continue

        score = float(scores[index])

        if not np.isfinite(score):
            continue

        results.append({
            "id": movie.id,
            "title": movie.title,
            "overview": movie.overview,
            "similarity_score": round(score, 4)
        })

    # Step 9: Rank by similarity
    results.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return results[:limit]
