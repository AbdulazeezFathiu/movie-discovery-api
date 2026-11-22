
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from movies.models import Movie

import numpy as np

from movies.models import MovieEmbedding

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer(MODEL_NAME)


@lru_cache(maxsize=1)
def get_movie_embeddings(cache_version):
    movies = list(
        Movie.objects.exclude(overview="")
        .exclude(overview__isnull=True)
        .order_by("id")
    )

    if not movies:
        return [], None

    descriptions = [
        movie.overview for movie in movies
    ]

    model = get_embedding_model()

    embeddings = model.encode_document(
        descriptions,
        normalize_embeddings=True
    )

    return movies, embeddings





def semantic_movie_search(query, limit=5):
    if not query or not query.strip():
        return []

    # Load stored embeddings from PostgreSQL
    records = list(
        MovieEmbedding.objects
        .select_related("movie")
        .filter(model_name=MODEL_NAME)
        .order_by("movie_id")
    )

    if not records:
        return []

    # Ignore stale embeddings
    records = [
        record for record in records
        if record.source_updated_at == record.movie.updated_at
        and len(record.vector) == 384
    ]

    if not records:
        return []

    # Convert stored JSON vectors into a NumPy matrix
    movie_embeddings = np.asarray(
        [record.vector for record in records],
        dtype=np.float32
    )

    # Encode only the user's query
    model = get_embedding_model()

    query_embedding = model.encode_query(
        query,
        normalize_embeddings=True
    )

    # Calculate cosine similarity
    similarity_scores = np.dot(
        movie_embeddings,
        query_embedding
    )

    results = []

    for index, score in enumerate(similarity_scores):
        results.append({
            "id": records[index].movie.id,
            "title": records[index].movie.title,
            "overview": records[index].movie.overview,
            "similarity_score": round(float(score), 4)
        })

    results.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return results[:limit]
