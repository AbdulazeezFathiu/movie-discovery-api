from django.urls import path
from . import views
from .views import WatchlistView, WatchlistDetailView
from .views import MovieReviewView, ReviewDetailView
from .views import WatchedMovieView, WatchedMovieDetailView
from .views import MovieRecommendationView
from .views import NaturalLanguageSearchView
from .views import SemanticSearchView
from .views import MoodRecommendationView
from .views import PersonalizedRecommendationView

urlpatterns = [
    path('welcome/', views.welcome, name='welcome'),
    path('movies/', views.movie_list, name='movie-list'),
    path(
        "movies/hybrid-search/",
        views.hybrid_search_view,
        name="hybrid-search"
    ),
    path('movies/<int:pk>/', views.movie_detail, name='movie-detail'),
    path(
        'watchlist/',
        WatchlistView.as_view(),
        name='watchlist'
    ),

    path(
        'watchlist/<int:movie_id>/',
        WatchlistDetailView.as_view(),
        name='watchlist-detail'
    ),
    path(
        "movies/<int:movie_id>/reviews/",
        MovieReviewView.as_view(),
        name="movie-reviews"
    ),

    path(
        "reviews/<int:review_id>/",
        ReviewDetailView.as_view(),
        name="review-detail"
    ),
    path(
        "watched/",
        WatchedMovieView.as_view(),
        name="watched-movies"
    ),

    path(
        "watched/<int:movie_id>/",
        WatchedMovieDetailView.as_view(),
        name="watched-movie-detail"
    ),
    path(
        "movies/<int:movie_id>/recommendations/",
        MovieRecommendationView.as_view(),
        name="movie-recommendations"
    ),
    path(
        "movies/nlp-search/",
        NaturalLanguageSearchView.as_view(),
        name="nlp-movie-search"
    ),
    path(
        "movies/semantic-search/",
        SemanticSearchView.as_view(),
        name="semantic-search"
    ),
    path(
        "movies/mood/",
        MoodRecommendationView.as_view(),
        name="mood-recommendations"
    ),
    path(
        "movies/for-you/",
        PersonalizedRecommendationView.as_view(),
        name="personalized-recommendations"
    ),

    ]
