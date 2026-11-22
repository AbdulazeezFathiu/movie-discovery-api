from rest_framework import serializers
from .models import Movie, Genre, Actor
from .models import Watchlist
from .models import Review
from .models import WatchedMovie

class MovieSerializer(serializers.ModelSerializer):

    genres = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        write_only=True
    )

    genre_names = serializers.StringRelatedField(
        source='genres',
        many=True,
        read_only=True
    )
    actor_names = serializers.StringRelatedField(
        source='actors',
        many=True,
        read_only=True
    )
    director_names = serializers.StringRelatedField(
        source='director',
        read_only=True
    )

    class Meta:
        model = Movie
        fields = '__all__'


class WatchlistSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = Watchlist
        fields = ['id', 'movie', 'added_at']


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "movie",
            "username",
            "rating",
            "comment",
            "created_at",
            "updated_at"
        ]

        read_only_fields = [
            "id",
            "movie",
            "username",
            "created_at",
            "updated_at"
        ]

    def validate_rating(self, value):
        if not 1 <= value <= 10:
            raise serializers.ValidationError(
                "Rating must be between 1 and 10."
            )

        return value

class WatchedMovieSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = WatchedMovie
        fields = ["id", "movie", "watched_at"]