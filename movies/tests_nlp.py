
from django.test import TestCase

from movies.models import Movie
from movies.nlp.recommendation import recommend_similar_movies
from movies.nlp.search import natural_language_search


class NLPRecommendationTests(TestCase):

    def setUp(self):
        self.space_movie = Movie.objects.create(
            title="Space Exploration",
            overview=(
                "Astronauts explore distant planets "
                "during a dangerous space mission."
            ),
            release_date="2020-01-01",
            runtime=120,
            original_language="en"
        )

        self.similar_movie = Movie.objects.create(
            title="Planet Mission",
            overview=(
                "Astronauts travel through space "
                "to explore distant planets."
            ),
            release_date="2021-01-01",
            runtime=110,
            original_language="en"
        )

        self.horror_movie = Movie.objects.create(
            title="Haunted Mansion",
            overview=(
                "A terrifying ghost haunts an "
                "abandoned mansion at night."
            ),
            release_date="2022-01-01",
            runtime=100,
            original_language="en"
        )

    def test_recommend_similar_movies(self):
        results = recommend_similar_movies(
            self.space_movie.id,
            limit=2
        )

        self.assertEqual(len(results), 2)

        self.assertEqual(
            results[0]["id"],
            self.similar_movie.id
        )

    def test_exclude_selected_movie(self):
        results = recommend_similar_movies(
            self.space_movie.id
        )

        recommended_ids = [
            item["id"] for item in results
        ]

        self.assertNotIn(
            self.space_movie.id,
            recommended_ids
        )

    def test_recommendation_limit(self):
        results = recommend_similar_movies(
            self.space_movie.id,
            limit=1
        )

        self.assertEqual(len(results), 1)

    def test_invalid_movie_id(self):
        results = recommend_similar_movies(
            movie_id=999999
        )

        self.assertEqual(results, [])

    def test_natural_language_search(self):
        results = natural_language_search(
            "astronauts exploring distant planets",
            limit=3
        )

        self.assertTrue(len(results) > 0)

        self.assertEqual(
            results[0]["id"],
            self.similar_movie.id
        )

    def test_unrelated_query(self):
        results = natural_language_search(
            "quantum banana pineapple",
            limit=3
        )

        self.assertEqual(results, [])
class EmptyNLPDatabaseTests(TestCase):

    def test_empty_recommendations(self):
        results = recommend_similar_movies(
            movie_id=1
        )

        self.assertEqual(results, [])

    def test_empty_natural_language_search(self):
        results = natural_language_search(
            "space exploration"
        )

        self.assertEqual(results, [])