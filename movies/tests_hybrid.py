
from unittest.mock import patch

import numpy as np

from django.test import TestCase

from movies.models import Movie, MovieEmbedding
from movies.nlp.hybrid import hybrid_movie_search
from movies.nlp.semantic_search import MODEL_NAME


class HybridSearchTests(TestCase):

    def setUp(self):
        self.movies = [
            Movie.objects.create(
                title="Space Exploration",
                overview=(
                    "Astronauts explore distant planets "
                    "and discover alien worlds."
                ),
                runtime=120,
                original_language="en"
            ),
            Movie.objects.create(
                title="Haunted Mansion",
                overview=(
                    "A family encounters terrifying "
                    "ghosts inside a haunted house."
                ),
                runtime=110,
                original_language="en"
            ),
            Movie.objects.create(
                title="Ocean Adventure",
                overview=(
                    "Sailors travel across the ocean "
                    "in search of hidden treasures."
                ),
                runtime=100,
                original_language="en"
            ),
        ]

        self.create_embedding(
            self.movies[0], [1.0, 0.0, 0.0]
        )

        self.create_embedding(
            self.movies[1], [0.0, 1.0, 0.0]
        )

        self.create_embedding(
            self.movies[2], [0.0, 0.0, 1.0]
        )

        # Artificial normalized query vector
        self.query_vector = np.zeros(
            384, dtype=np.float32
        )
        self.query_vector[0] = 1.0

    def create_embedding(self, movie, values):
        vector = np.zeros(
            384, dtype=np.float32
        )

        vector[:len(values)] = values

        vector = vector / np.linalg.norm(vector)

        MovieEmbedding.objects.create(
            movie=movie,
            vector=vector.tolist(),
            model_name=MODEL_NAME,
            source_updated_at=movie.updated_at
        )

    @patch("movies.nlp.hybrid.encode_query_onnx")
    def test_hybrid_search_ranking(self, mock_encoder):
        mock_encoder.return_value = self.query_vector

        results = hybrid_movie_search(
            "astronauts exploring distant planets",
            limit=3
        )

        self.assertEqual(len(results), 3)

        self.assertEqual(
            results[0]["title"],
            "Space Exploration"
        )

        self.assertGreater(
            results[0]["hybrid_score"],
            results[1]["hybrid_score"]
        )

    @patch("movies.nlp.hybrid.encode_query_onnx")
    def test_hybrid_search_limit(self, mock_encoder):
        mock_encoder.return_value = self.query_vector

        results = hybrid_movie_search(
            "space exploration",
            limit=2
        )

        self.assertEqual(len(results), 2)

    def test_empty_query(self):
        results = hybrid_movie_search("")

        self.assertEqual(results, [])

    @patch("movies.nlp.hybrid.encode_query_onnx")
    def test_hybrid_scores_present(self, mock_encoder):
        mock_encoder.return_value = self.query_vector

        results = hybrid_movie_search(
            "astronauts exploring planets",
            limit=3
        )

        for movie in results:
            self.assertIn("semantic_score", movie)
            self.assertIn("keyword_score", movie)
            self.assertIn("hybrid_score", movie)

    @patch("movies.nlp.hybrid.encode_query_onnx")
    def test_keyword_matching(self, mock_encoder):
        mock_encoder.return_value = self.query_vector

        results = hybrid_movie_search(
            "astronauts exploring planets",
            limit=3
        )

        space_movie = next(
            movie for movie in results
            if movie["title"] == "Space Exploration"
        )

        haunted_movie = next(
            movie for movie in results
            if movie["title"] == "Haunted Mansion"
        )

        self.assertGreater(
            space_movie["keyword_score"],
            haunted_movie["keyword_score"]
        )

    @patch("movies.nlp.hybrid.encode_query_onnx")
    def test_no_embeddings(self, mock_encoder):
        MovieEmbedding.objects.all().delete()

        results = hybrid_movie_search(
            "space exploration"
        )

        self.assertEqual(results, [])
        mock_encoder.assert_not_called()
