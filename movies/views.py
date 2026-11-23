from django.shortcuts import get_object_or_404
from django.db.models import Q
from .nlp.search import natural_language_search
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .nlp.recommendation import recommend_similar_movies
from .models import Movie, Watchlist, Review, WatchedMovie
from rest_framework import serializers
from .serializers import (
    MovieSerializer,
    WatchlistSerializer,
    ReviewSerializer,
    WatchedMovieSerializer,
)
from rest_framework.pagination import PageNumberPagination
from .nlp.semantic_search import semantic_movie_search
from .nlp.mood import recommend_by_mood, MOOD_DESCRIPTIONS
from .nlp.personalized import personalized_recommendations
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
    OpenApiParameter,
    OpenApiTypes,
)
@extend_schema(
    operation_id="api_welcome",
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["GET"])
def welcome(request):

    return Response({
        "message": "Welcome to Movie Discovery API!",
        "status": "success"
    })


@extend_schema_view(
    get=extend_schema(
        operation_id="list_movies",
        responses={200: OpenApiTypes.OBJECT},
    ),
    post=extend_schema(
        operation_id="create_movie",
        request=MovieSerializer,
        responses={201: MovieSerializer},
    ),
)
@api_view(["GET", "POST"])
def movie_list(request):
    # Keep your existing code
    if request.method == 'GET':

        search_query = request.query_params.get('search', '').strip()

        movies = Movie.objects.select_related(
            "director"
        ).prefetch_related(
            "genres",
            "actors"
        )

        if search_query:
            movies = movies.filter(
                Q(title__icontains=search_query) |
                Q(overview__icontains=search_query)
            )
        genre = request.query_params.get('genre', '').strip()

        if genre:
            movies = movies.filter(genres__name__iexact=genre).distinct()

        language = request.query_params.get('language', '').strip()

        if language:
            movies = movies.filter(original_language__iexact=language)

        ordering = request.query_params.get('ordering')

        allowed_ordering = [
            'title',
            '-title',
            'release_date',
            '-release_date',
            'runtime',
            '-runtime'
        ]

        if ordering in allowed_ordering:
            movies = movies.order_by(ordering)
        paginator = PageNumberPagination()
        paginator.page_size = 10

        paginated_movies = paginator.paginate_queryset(movies, request)

        serializer = MovieSerializer(paginated_movies, many=True)

        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        serializer = MovieSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="retrieve_movie",
        responses={200: MovieSerializer},
    ),
    put=extend_schema(
        operation_id="update_movie",
        request=MovieSerializer,
        responses={200: MovieSerializer},
    ),
    patch=extend_schema(
        operation_id="partial_update_movie",
        request=MovieSerializer,
        responses={200: MovieSerializer},
    ),
    delete=extend_schema(
        operation_id="delete_movie",
        responses={204: None},
    ),
)
@api_view(["GET", "PUT", "PATCH", "DELETE"])
def movie_detail(request, pk):
    # Keep your existing code

    movie = get_object_or_404(Movie, pk=pk)

    if request.method == 'GET':
        serializer = MovieSerializer(movie)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = MovieSerializer(movie, data=request.data)

    elif request.method == 'PATCH':
        serializer = MovieSerializer(
            movie,
            data=request.data,
            partial=True
        )
    elif request.method == 'DELETE':
        movie.delete()

        return Response(
            {"message": "Movie deleted successfully"},
            status=status.HTTP_200_OK
        )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

@extend_schema_view(
    get=extend_schema(
        responses=WatchlistSerializer(many=True)
    ),
    post=extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={201: WatchlistSerializer}
    ),
)
class WatchlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        watchlist = Watchlist.objects.filter(
            user=request.user
        ).select_related('movie')

        serializer = WatchlistSerializer(
            watchlist,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):
        movie_id = request.data.get('movie_id')

        if not movie_id:
            return Response(
                {"error": "movie_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            movie = Movie.objects.get(id=movie_id)
        except (Movie.DoesNotExist, ValueError, TypeError):
            return Response(
                {"error": "Movie not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        watchlist, created = Watchlist.objects.get_or_create(
            user=request.user,
            movie=movie
        )

        if not created:
            return Response(
                {"message": "Movie already in watchlist."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = WatchlistSerializer(watchlist)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    delete=extend_schema(responses={204: None})
)
class WatchlistDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, movie_id):
        deleted_count, _ = Watchlist.objects.filter(
            user=request.user,
            movie_id=movie_id
        ).delete()

        if deleted_count == 0:
            return Response(
                {"error": "Movie not found in your watchlist."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema_view(
    get=extend_schema(
        responses=ReviewSerializer(many=True)
    ),
    post=extend_schema(
        request=ReviewSerializer,
        responses={201: ReviewSerializer}
    ),
)
class MovieReviewView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, movie_id):
        get_object_or_404(Movie, id=movie_id)

        reviews = Review.objects.filter(
            movie_id=movie_id
        ).select_related("user").order_by("-created_at")

        serializer = ReviewSerializer(reviews, many=True)

        return Response(serializer.data)

    def post(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)

        if Review.objects.filter(
            user=request.user,
            movie=movie
        ).exists():
            return Response(
                {"error": "You have already reviewed this movie."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReviewSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        serializer.save(
            user=request.user,
            movie=movie
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    patch=extend_schema(
        request=ReviewSerializer,
        responses={200: ReviewSerializer}
    ),
    delete=extend_schema(responses={204: None}),
)
class ReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, review_id):
        review = get_object_or_404(
            Review,
            id=review_id,
            user=request.user
        )

        serializer = ReviewSerializer(
            review,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def delete(self, request, review_id):
        review = get_object_or_404(
            Review,
            id=review_id,
            user=request.user
        )

        review.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema_view(
    get=extend_schema(
        responses=WatchedMovieSerializer(many=True)
    ),
    post=extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={201: WatchedMovieSerializer}
    ),
)
class WatchedMovieView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        watched_movies = WatchedMovie.objects.filter(
            user=request.user
        ).select_related("movie").order_by("-watched_at")

        serializer = WatchedMovieSerializer(
            watched_movies,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):
        movie_id = request.data.get("movie_id")

        if not movie_id:
            return Response(
                {"error": "movie_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        movie = get_object_or_404(Movie, id=movie_id)

        watched, created = WatchedMovie.objects.get_or_create(
            user=request.user,
            movie=movie
        )

        if not created:
            return Response(
                {"message": "Movie already marked as watched."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = WatchedMovieSerializer(watched)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    delete=extend_schema(responses={204: None})
)
class WatchedMovieDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, movie_id):
        deleted_count, _ = WatchedMovie.objects.filter(
            user=request.user,
            movie_id=movie_id
        ).delete()

        if deleted_count == 0:
            return Response(
                {"error": "Movie is not in your watched history."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="movie_recommendations",
        summary="Get similar movie recommendations",
        responses={
            200: inline_serializer(
                name="MovieRecommendationResponse",
                fields={
                    "movie": serializers.CharField(),
                    "count": serializers.IntegerField(),
                    "recommendations": serializers.ListField(
                        child=serializers.DictField()
                    ),
                },
            )
        },
    )
)
class MovieRecommendationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)

        # Read the limit from query parameters
        limit = request.query_params.get("limit", 5)

        try:
            limit = int(limit)
        except (ValueError, TypeError):
            return Response(
                {"error": "Limit must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if limit < 1 or limit > 20:
            return Response(
                {"error": "Limit must be between 1 and 20."},
                status=status.HTTP_400_BAD_REQUEST
            )

        recommendations = recommend_similar_movies(
            movie_id=movie.id,
            limit=limit
        )

        return Response({
            "movie": movie.title,
            "recommendations": recommendations,
            "count": len(recommendations)
        })


@extend_schema_view(
    get=extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
)
class NaturalLanguageSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        limit = request.query_params.get("limit", 10)

        if not query:
            return Response(
                {"error": "Search query is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            return Response(
                {"error": "Limit must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not 1 <= limit <= 20:
            return Response(
                {"error": "Limit must be between 1 and 20."},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = natural_language_search(
            query=query,
            limit=limit
        )

        return Response({
            "query": query,
            "count": len(results),
            "results": results
        })


@extend_schema_view(
    get=extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
)
class SemanticSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        limit = request.query_params.get("limit", 5)

        if not query:
            return Response(
                {"error": "Search query is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            limit = int(limit)
        except (ValueError, TypeError):
            return Response(
                {"error": "Limit must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not 1 <= limit <= 20:
            return Response(
                {"error": "Limit must be between 1 and 20."},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = semantic_movie_search(
            query=query,
            limit=limit
        )

        return Response({
            "query": query,
            "count": len(results),
            "search_type": "semantic",
            "results": results
        })


@extend_schema_view(
    get=extend_schema(
        operation_id="mood_recommendations",
        summary="Get movie recommendations by mood",
        responses={
            200: inline_serializer(
                name="MoodRecommendationResponse",
                fields={
                    "mood": serializers.CharField(),
                    "count": serializers.IntegerField(),
                    "recommendations": serializers.ListField(
                        child=serializers.DictField()
                    ),
                },
            )
        },
    )
)
class MoodRecommendationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        mood = request.query_params.get("mood", "").strip().lower()
        limit = request.query_params.get("limit", 5)

        if not mood:
            return Response(
                {"error": "Mood is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if mood not in MOOD_DESCRIPTIONS:
            return Response(
                {
                    "error": "Unsupported mood.",
                    "available_moods": list(MOOD_DESCRIPTIONS.keys())
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            limit = int(limit)
        except (ValueError, TypeError):
            return Response(
                {"error": "Limit must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not 1 <= limit <= 20:
            return Response(
                {"error": "Limit must be between 1 and 20."},
                status=status.HTTP_400_BAD_REQUEST
            )

        recommendations = recommend_by_mood(
            mood=mood,
            limit=limit
        )

        return Response({
            "mood": mood,
            "count": len(recommendations),
            "recommendations": recommendations
        })


@extend_schema_view(
    get=extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
)
class PersonalizedRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = request.query_params.get("limit", 5)

        try:
            limit = int(limit)
        except (ValueError, TypeError):
            return Response(
                {"error": "Limit must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not 1 <= limit <= 20:
            return Response(
                {"error": "Limit must be between 1 and 20."},
                status=status.HTTP_400_BAD_REQUEST
            )

        recommendations = personalized_recommendations(
            user=request.user,
            limit=limit
        )

        return Response({
            "user": request.user.username,
            "recommendation_type": "personalized",
            "count": len(recommendations),
            "recommendations": recommendations
        })
