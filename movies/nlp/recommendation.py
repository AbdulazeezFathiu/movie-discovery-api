
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from movies.models import Movie
from .preprocessing import preprocess_text


def recommend_similar_movies(movie_id, limit=5):

    movies = list(
        Movie.objects.exclude(overview="")
        .order_by("id")
    )

    if len(movies) < 2:
        return []

    # Prepare movie descriptions
    descriptions = [
        preprocess_text(movie.overview)
        for movie in movies
    ]

    # Convert text to numerical vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(descriptions)

    # Find the selected movie in the dataset
    movie_index = next(
        (index for index, movie in enumerate(movies)
         if movie.id == movie_id),
        None
    )

    if movie_index is None:
        return []

    # Compare selected movie against all others
    similarity_scores = cosine_similarity(
        tfidf_matrix[movie_index],
        tfidf_matrix
    ).flatten()

    recommendations = []

    for index, score in enumerate(similarity_scores):
        if index != movie_index:
            recommendations.append({
                "id": movies[index].id,
                "title": movies[index].title,
                "similarity_score": round(float(score), 4)
            })

    # Highest similarity first
    recommendations.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return recommendations[:limit]
