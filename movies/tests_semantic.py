
from unittest.mock import patch, Mock

import numpy as np

from django.test import TestCase
from django.contrib.auth import get_user_model

from movies.models import (
    Movie,
    Review,
    Watchlist,
    WatchedMovie,
    MovieEmbedding,
)

from movies.nlp.semantic_search import (
    semantic_movie_search,
    MODEL_NAME,
)

from movies.nlp.personalized import (
    personalized_recommendations,
)


class SemanticRecommendationTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="nlpuser",
            password="StrongPassword123!"
        )

        # Create four test movies
        self.movies = [
            Movie.objects.create(
                title="Space Exploration",
                overview="Astronauts explore distant planets.",
                runtime=120,
                original_language="en"
            ),
            Movie.objects.create(
                title="Planet Mission",
                overview="A mission through outer space.",
                runtime=110,
                original_language="en"
            ),
            Movie.objects.create(
                title="Haunted Mansion",
                overview="A terrifying ghost story.",
                runtime=100,
                original_language="en"
            ),
            Movie.objects.create(
                title="Galactic Adventure",
                overview="Explorers travel across galaxies.",
                runtime=115,
                original_language="en"
            ),
        ]

        # Store fake embeddings in the test database
        self.create_test_embedding(
            self.movies[0], [1.0, 0.0, 0.0]
        )

        self.create_test_embedding(
            self.movies[1], [0.8, 0.6, 0.0]
        )

        self.create_test_embedding(
            self.movies[2], [0.0, 0.0, 1.0]
        )

        self.create_test_embedding(
            self.movies[3], [0.6, 0.8, 0.0]
        )

    def create_test_embedding(self, movie, values):
        """
        Create a normalized 384-dimensional embedding.
        """

        vector = np.zeros(384, dtype=np.float32)

        vector[:len(values)] = values

        norm = np.linalg.norm(vector)

        if norm > 0:
            vector = vector / norm

        MovieEmbedding.objects.update_or_create(
            movie=movie,
            defaults={
                "vector": vector.tolist(),
                "model_name": MODEL_NAME,
                "source_updated_at": movie.updated_at,
            },
        )

    def test_semantic_search_ranking(self):
        fake_model = Mock()

        query_vector = np.zeros(
            384, dtype=np.float32
        )

        query_vector[0] = 1.0

        fake_model.encode_query.return_value = (
            query_vector
        )

        with patch(
                "movies.nlp.semantic_search.encode_query_onnx",
                return_value=query_vector
        ):
            results = semantic_movie_search(
                "space exploration",
                limit=4
            )

        self.assertEqual(len(results), 4)

        self.assertEqual(
            results[0]["title"],
            "Space Exploration"
        )

        self.assertEqual(
            results[1]["title"],
            "Planet Mission"
        )

        self.assertEqual(
            results[2]["title"],
            "Galactic Adventure"
        )

        self.assertEqual(
            results[3]["title"],
            "Haunted Mansion"
        )

    def test_semantic_search_limit(self):
        fake_model = Mock()

        query_vector = np.zeros(
            384, dtype=np.float32
        )

        query_vector[0] = 1.0

        fake_model.encode_query.return_value = (
            query_vector
        )

        with patch(
                "movies.nlp.semantic_search.encode_query_onnx",
                return_value=query_vector
        ):
            results = semantic_movie_search(
                "space exploration",
                limit=2
            )

        self.assertEqual(len(results), 2)

    def test_empty_semantic_query(self):
        results = semantic_movie_search("")

        self.assertEqual(results, [])

    def test_personalized_recommendation_ranking(self):

        # User strongly likes Space Exploration
        Review.objects.create(
            user=self.user,
            movie=self.movies[0],
            rating=10
        )

        results = personalized_recommendations(
            self.user,
            limit=3
        )

        self.assertEqual(len(results), 3)

        self.assertEqual(
            results[0]["title"],
            "Planet Mission"
        )

        recommended_ids = [
            item["id"] for item in results
        ]

        # Already rated movies must be excluded
        self.assertNotIn(
            self.movies[0].id,
            recommended_ids
        )

    def test_personalized_excludes_known_movies(self):

        # Rated movie
        Review.objects.create(
            user=self.user,
            movie=self.movies[0],
            rating=9
        )

        # Watchlisted movie
        Watchlist.objects.create(
            user=self.user,
            movie=self.movies[1]
        )

        # Watched movie
        WatchedMovie.objects.create(
            user=self.user,
            movie=self.movies[2]
        )

        results = personalized_recommendations(
            self.user,
            limit=5
        )

        recommended_ids = [
            item["id"] for item in results
        ]

        self.assertNotIn(
            self.movies[0].id,
            recommended_ids
        )

        self.assertNotIn(
            self.movies[1].id,
            recommended_ids
        )

        self.assertNotIn(
            self.movies[2].id,
            recommended_ids
        )

        # Only Galactic Adventure remains
        self.assertEqual(
            recommended_ids,
            [self.movies[3].id]
        )

    def test_user_without_preferences(self):

        results = personalized_recommendations(
            self.user
        )

        self.assertEqual(results, [])
