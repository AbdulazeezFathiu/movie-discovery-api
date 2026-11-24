
from functools import lru_cache

import numpy as np

from movies.models import Movie, MovieEmbedding
from movies.nlp.onnx_encoder import encode_query_onnx


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Legacy model loader.

    Used by the offline embedding-generation command,
    not by the live semantic-search endpoint.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        MODEL_NAME,
        device="cpu"
    )


@lru_cache(maxsize=1)
def get_movie_embeddings(cache_version):
    """
    Legacy in-memory embeddings.

    Retained temporarily for backward compatibility.
    """
    movies = list(
        Movie.objects
        .exclude(overview="")
        .exclude(overview__isnull=True)
        .order_by("id")
    )

    if not movies:
        return [], None

    model = get_embedding_model()

    embeddings = model.encode_document(
        [movie.overview for movie in movies],
        normalize_embeddings=True
    )

    return movies, embeddings


def semantic_movie_search(query, limit=5):
    """
    Search movies using:
    - PostgreSQL-stored movie embeddings
    - ONNX Runtime query embedding generation
    - Cosine similarity ranking
    """

    if not isinstance(query, str) or not query.strip():
        return []

    # Validate result limit
    limit = max(1, int(limit))

    # Retrieve saved movie embeddings
    records = list(
        MovieEmbedding.objects
        .select_related("movie")
        .filter(model_name=MODEL_NAME)
        .order_by("movie_id")
    )

    # Filter outdated or invalid embeddings
    valid_records = [
        record
        for record in records
        if (
            record.source_updated_at
            == record.movie.updated_at
            and isinstance(record.vector, list)
            and len(record.vector) == EMBEDDING_DIMENSION
        )
    ]

    if not valid_records:
        return []

    # Movie embeddings from PostgreSQL
    movie_embeddings = np.asarray(
        [record.vector for record in valid_records],
        dtype=np.float32
    )

    # Generate query embedding using ONNX
    # No PyTorch or Sentence Transformers required here
    query_embedding = encode_query_onnx(query)

    # Calculate similarity
    similarity_scores = np.dot(
        movie_embeddings,
        query_embedding
    )

    # Prepare results
    results = []

    for record, score in zip(
        valid_records,
        similarity_scores
    ):
        if not np.isfinite(score):
            continue

        results.append({
            "id": record.movie.id,
            "title": record.movie.title,
            "overview": record.movie.overview,
            "similarity_score": round(float(score), 4)
        })

    # Highest similarity first
    results.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return results[:limit]
