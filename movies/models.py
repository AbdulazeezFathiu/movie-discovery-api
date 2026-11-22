from django.db import models
from django.conf import settings

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Actor(models.Model):
    name = models.CharField(max_length=150)
    bio = models.TextField(blank=True)
    profile_url = models.URLField(blank=True, default="")

    def __str__(self):
        return self.name
class Director(models.Model):
    name = models.CharField(max_length=150)
    bio = models.TextField(blank=True)
    profile_url = models.URLField(blank=True, default="")

    def __str__(self):
        return self.name
class Movie(models.Model):
    title = models.CharField(max_length=255)
    overview = models.TextField()
    release_date = models.DateField(null=True, blank=True)
    runtime = models.PositiveIntegerField()
    original_language = models.CharField(max_length=50)

    poster_url = models.URLField(blank=True, default="")
    backdrop_url = models.URLField(blank=True)

    genres = models.ManyToManyField(
        Genre,
        related_name="movies"
    )
    actors = models.ManyToManyField(
        Actor,
        related_name='movies',
        blank=True
    )
    director = models.ForeignKey(
        Director,
        on_delete=models.SET_NULL,
        related_name='movies',
        null=True,
        blank=True
    )
    tmdb_id = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True
    )

    rating = models.FloatField(default=0.0)

    vote_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["release_date"],
                name="movie_release_idx"
            ),
            models.Index(
                fields=["created_at"],
                name="movie_created_idx"
            ),
        ]
    def __str__(self):
        return self.title


class Watchlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watchlist'
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='watchlisted_by'
    )

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'movie'],
                name='unique_user_movie_watchlist'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"
class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    rating = models.PositiveSmallIntegerField()

    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "movie"],
                name="unique_user_movie_review"
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=10),
                name="review_rating_between_1_and_10"
            ),
        ]

    def __str__(self):
        return f"{self.user.username} rated {self.movie.title}: {self.rating}/10"

class WatchedMovie(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watched_movies"
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="watched_by"
    )

    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "movie"],
                name="unique_user_watched_movie"
            )
        ]

    def __str__(self):
        return f"{self.user.username} watched {self.movie.title}"

class MovieEmbedding(models.Model):
        movie = models.OneToOneField(
            Movie,
            on_delete=models.CASCADE,
            related_name="embedding_record"
        )

        vector = models.JSONField()

        model_name = models.CharField(
            max_length=150,
            default="sentence-transformers/all-MiniLM-L6-v2"
        )

        source_updated_at = models.DateTimeField()

        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        def __str__(self):
            return f"Embedding for {self.movie.title}"
