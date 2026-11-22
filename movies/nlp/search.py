
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from movies.models import Movie
from .preprocessing import preprocess_text


def natural_language_search(query, limit=10):

    # Step 1: Clean the user's search query
    cleaned_query = preprocess_text(query)

    if not cleaned_query:
        return []

    # Step 2: Retrieve movies with descriptions
    movies = list(
        Movie.objects.exclude(overview="")
        .order_by("id")
    )

    if not movies:
        return []

    # Step 3: Preprocess movie descriptions
    descriptions = [
        preprocess_text(movie.overview)
        for movie in movies
    ]

    # Step 4: Convert movie descriptions into vectors
    vectorizer = TfidfVectorizer()

    try:
        movie_vectors = vectorizer.fit_transform(descriptions)
    except ValueError:
        # No usable vocabulary in the descriptions
        return []

    # Step 5: Convert the user's query using the same vocabulary
    query_vector = vectorizer.transform([cleaned_query])

    # Step 6: Compare query against movie descriptions
    similarity_scores = cosine_similarity(
        query_vector,
        movie_vectors
    ).flatten()

    # Step 7: Build search results
    results = []

    for index, score in enumerate(similarity_scores):

        if score > 0:
            results.append({
                "id": movies[index].id,
                "title": movies[index].title,
                "overview": movies[index].overview,
                "similarity_score": round(float(score), 4)
            })

    # Step 8: Sort from highest relevance to lowest
    results.sort(
        key=lambda movie: movie["similarity_score"],
        reverse=True
    )

    return results[:limit]
