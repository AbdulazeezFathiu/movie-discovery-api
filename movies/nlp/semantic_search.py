
from functools import lru_cache

import numpy as np

from movies.models import Movie, MovieEmbedding


# Sentence Transformer model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the Sentence Transformer model only when needed.

    This avoids importing PyTorch and Sentence Transformers
    during normal Django startup.
    """

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        MODEL_NAME,
        device="cpu"
    )

    return model


@lru_cache(maxsize=1)
def get_movie_embeddings(cache_version):
    """
    Legacy in-memory embedding function.

    Kept for compatibility with existing code.
    New semantic search uses PostgreSQL embeddings.
    """

    movies = list(
        Movie.objects
        .exclude(overview="")
        .exclude(overview__isnull=True)
        .order_by("id")
    )

    if not movies:
        return [], None

    descriptions = [
        movie.overview
        for movie in movies
    ]

    model = get_embedding_model()

    embeddings = model.encode_document(
        descriptions,
        normalize_embeddings=True
    )

    return movies, embeddings


def semantic_movie_search(query, limit=5):
    """
    Search movies using embeddings stored in PostgreSQL.

    Only the user's query is encoded at request time.
    Movie embeddings are retrieved from the database.
    """

    # Step 1: Validate the search query
    if not query or not query.strip():
        return []

    # Step 2: Retrieve stored embeddings
    records = list(
        MovieEmbedding.objects
        .select_related("movie")
        .filter(model_name=MODEL_NAME)
        .order_by("movie_id")
    )

    if not records:
        return []

    # Step 3: Filter outdated or invalid embeddings
    valid_records = []

    for record in records:

        if record.source_updated_at != record.movie.updated_at:
            continue

        if not isinstance(record.vector, list):
            continue

        if len(record.vector) != EMBEDDING_DIMENSION:
            continue

        valid_records.append(record)

    if not valid_records:
        return []

    # Step 4: Convert stored vectors to NumPy
    movie_embeddings = np.asarray(
        [record.vector for record in valid_records],
        dtype=np.float32
    )

    # Step 5: Load model only when required
    model = get_embedding_model()

    # Step 6: Encode the search query
    query_embedding = np.asarray(
        model.encode_query(
            query,
            normalize_embeddings=True
        ),
        dtype=np.float32
    )

    # Step 7: Calculate similarity scores
    similarity_scores = np.dot(
        movie_embeddings,
        query_embedding
    )

    # Step 8: Build search results
    results = []

    for index, score in enumerate(similarity_scores):

        movie = valid_records[index].movie

        results.append({
            "id": movie.id,
            "title": movie.title,
            "overview": movie.overview,
            "similarity_score": round(
                float(score),
                4
            )
        })

    # Step 9: Rank by similarity
    results.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    # Step 10: Return top matches
    return results[:limit]
