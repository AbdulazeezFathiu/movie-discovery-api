

# Create your tests here.
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Review
from .models import Movie, Watchlist
from .models import WatchedMovie
User = get_user_model()


class AuthenticationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!"
        )

    def test_login_success(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_password(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "WrongPassword123!"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

class WatchlistTests(APITestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="movieuser",
            password="StrongPassword123!"
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            password="StrongPassword123!"
        )

        self.movie = Movie.objects.create(
            title="Test Space Movie",
            overview="Astronauts explore distant planets.",
            release_date="2020-01-01",
            runtime=120,
            original_language="en"
        )

        self.url = "/api/watchlist/"

        self.client.force_authenticate(user=self.user)

    def test_add_movie_to_watchlist(self):
        response = self.client.post(
            self.url,
            {"movie_id": self.movie.id},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            Watchlist.objects.filter(
                user=self.user,
                movie=self.movie
            ).exists()
        )

    def test_get_watchlist(self):
        Watchlist.objects.create(
            user=self.user,
            movie=self.movie
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(len(response.data), 1)

    def test_duplicate_watchlist(self):
        Watchlist.objects.create(
            user=self.user,
            movie=self.movie
        )

        response = self.client.post(
            self.url,
            {"movie_id": self.movie.id},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_unauthenticated_user(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.url,
            {"movie_id": self.movie.id},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_remove_movie_from_watchlist(self):
        Watchlist.objects.create(
            user=self.user,
            movie=self.movie
        )

        response = self.client.delete(
            f"/api/watchlist/{self.movie.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            Watchlist.objects.filter(
                user=self.user,
                movie=self.movie
            ).exists()
        )

    def test_cannot_delete_another_users_watchlist(self):
        Watchlist.objects.create(
            user=self.other_user,
            movie=self.movie
        )

        response = self.client.delete(
            f"/api/watchlist/{self.movie.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        self.assertTrue(
            Watchlist.objects.filter(
                user=self.other_user,
                movie=self.movie
            ).exists()
        )
class ReviewTests(APITestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="reviewuser",
            password="StrongPassword123!"
        )

        self.other_user = User.objects.create_user(
            username="anotheruser",
            password="StrongPassword123!"
        )

        self.movie = Movie.objects.create(
            title="Test Movie",
            overview="A science fiction adventure.",
            release_date="2020-01-01",
            runtime=120,
            original_language="en"
        )

        self.url = f"/api/movies/{self.movie.id}/reviews/"

        self.client.force_authenticate(user=self.user)

    def test_create_review(self):
        response = self.client.post(
            self.url,
            {
                "rating": 9,
                "comment": "Excellent movie!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)

    def test_get_reviews(self):
        Review.objects.create(
            user=self.user,
            movie=self.movie,
            rating=8,
            comment="Great!"
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_duplicate_review(self):
        Review.objects.create(
            user=self.user,
            movie=self.movie,
            rating=8
        )

        response = self.client.post(
            self.url,
            {"rating": 9},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_rating(self):
        response = self.client.post(
            self.url,
            {"rating": 11},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_review(self):
        review = Review.objects.create(
            user=self.user,
            movie=self.movie,
            rating=7
        )

        response = self.client.patch(
            f"/api/reviews/{review.id}/",
            {"rating": 10},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        review.refresh_from_db()
        self.assertEqual(review.rating, 10)

    def test_delete_review(self):
        review = Review.objects.create(
            user=self.user,
            movie=self.movie,
            rating=8
        )

        response = self.client.delete(
            f"/api/reviews/{review.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=review.id).exists())

    def test_cannot_update_another_users_review(self):
        review = Review.objects.create(
            user=self.other_user,
            movie=self.movie,
            rating=8
        )

        response = self.client.patch(
            f"/api/reviews/{review.id}/",
            {"rating": 10},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        review.refresh_from_db()
        self.assertEqual(review.rating, 8)

    def test_unauthenticated_review(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.url,
            {"rating": 9},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class WatchedMovieTests(APITestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="watcheduser",
            password="StrongPassword123!"
        )

        self.other_user = User.objects.create_user(
            username="seconduser",
            password="StrongPassword123!"
        )

        self.movie = Movie.objects.create(
            title="Interstellar Test",
            overview="Astronauts explore distant planets.",
            release_date="2014-11-07",
            runtime=169,
            original_language="en"
        )

        self.url = "/api/watched/"

        self.client.force_authenticate(user=self.user)

    def test_mark_movie_as_watched(self):
        response = self.client.post(
            self.url,
            {"movie_id": self.movie.id},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            WatchedMovie.objects.filter(
                user=self.user,
                movie=self.movie
            ).exists()
        )

    def test_get_watched_history(self):
        WatchedMovie.objects.create(
            user=self.user,
            movie=self.movie
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data), 1)

    def test_duplicate_watched_movie(self):
        WatchedMovie.objects.create(
            user=self.user,
            movie=self.movie
        )

        response = self.client.post(
            self.url,
            {"movie_id": self.movie.id},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_remove_watched_movie(self):
        WatchedMovie.objects.create(
            user=self.user,
            movie=self.movie
        )

        response = self.client.delete(
            f"/api/watched/{self.movie.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            WatchedMovie.objects.filter(
                user=self.user,
                movie=self.movie
            ).exists()
        )

    def test_cannot_remove_another_users_movie(self):
        WatchedMovie.objects.create(
            user=self.other_user,
            movie=self.movie
        )

        response = self.client.delete(
            f"/api/watched/{self.movie.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        self.assertTrue(
            WatchedMovie.objects.filter(
                user=self.other_user,
                movie=self.movie
            ).exists()
        )

    def test_unauthenticated_user(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.url,
            {"movie_id": self.movie.id},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_missing_movie_id(self):
        response = self.client.post(
            self.url,
            {},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_nonexistent_movie(self):
        response = self.client.post(
            self.url,
            {"movie_id": 999999},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )
