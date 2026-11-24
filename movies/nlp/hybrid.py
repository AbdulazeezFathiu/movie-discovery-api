
import numpy as np

from movies.models import MovieEmbedding
from movies.nlp.semantic_search import MODEL_NAME
from movies.nlp.onnx_encoder import encode_query_onnx


EMBEDDING_DIMENSION = 384

# Ranking weights
SEMANTIC_WEIGHT = 0.70
KEYWORD_WEIGHT = 0.30


def hybrid_movie_search(query, limit=5):
    """
    Hybrid movie search using:
    - ONNX semantic embeddings
    - TF-IDF keyword matching
    - Weighted score combination
    """

    if not isinstance(query, str) or not query.strip():
        return []

    limit = max(1, min(int(limit), 20))

    # Import only when hybrid search is used
    from sklearn.feature_extraction.text import TfidfVectorizer

    # Step 1: Retrieve stored embeddings
    records = list(
        MovieEmbedding.objects
        .select_related("movie")
        .prefetch_related("movie__genres")
        .filter(model_name=MODEL_NAME)
        .order_by("movie_id")
    )

    # Step 2: Keep valid embeddings
    valid_records = [
        record for record in records
        if (
            record.source_updated_at == record.movie.updated_at
            and isinstance(record.vector, list)
            and len(record.vector) == EMBEDDING_DIMENSION
        )
    ]

    if not valid_records:
        return []

    # Step 3: Prepare keyword-search documents
    documents = []

    for record in valid_records:
        movie = record.movie

        genres = " ".join(
            genre.name
            for genre in movie.genres.all()
        )

        document = (
            f"{movie.title} {movie.title} "
            f"{genres} {movie.overview or ''}"
        )

        documents.append(document)

    # Step 4: Calculate semantic similarity
    movie_vectors = np.asarray(
        [record.vector for record in valid_records],
        dtype=np.float32
    )

    query_vector = encode_query_onnx(query)

    semantic_scores = np.dot(
        movie_vectors,
        query_vector
    )

    # Step 5: Calculate keyword similarity
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        lowercase=True,
        sublinear_tf=True,
        max_features=10000
    )

    document_matrix = vectorizer.fit_transform(
        documents
    )

    query_matrix = vectorizer.transform([query])

    keyword_scores = (
        document_matrix @ query_matrix.T
    ).toarray().ravel()

    # Step 6: Combine scores
    results = []

    for index, record in enumerate(valid_records):

        semantic_score = float(
            semantic_scores[index]
        )

        keyword_score = float(
            keyword_scores[index]
        )

        if (
            not np.isfinite(semantic_score)
            or not np.isfinite(keyword_score)
        ):
            continue

        # Keep positive cosine similarity only
        semantic_relevance = np.clip(
            semantic_score,
            0.0,
            1.0
        )

        keyword_relevance = np.clip(
            keyword_score,
            0.0,
            1.0
        )

        # Weighted hybrid score
        hybrid_score = (
            SEMANTIC_WEIGHT * semantic_relevance
            + KEYWORD_WEIGHT * keyword_relevance
        )

        movie = record.movie

        results.append({
            "id": movie.id,
            "title": movie.title,
            "overview": movie.overview,
            "semantic_score": round(
                semantic_score, 4
            ),
            "keyword_score": round(
                keyword_score, 4
            ),
            "hybrid_score": round(
                float(hybrid_score), 4
            )
        })

    # Step 7: Sort by hybrid relevance
    results.sort(
        key=lambda item: item["hybrid_score"],
        reverse=True
    )

    return results[:limit]
