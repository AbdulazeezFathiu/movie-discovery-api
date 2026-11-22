from django.contrib import admin
from .models import Movie, Genre, Actor, Director

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'director',
        'release_date',
        'runtime',
        'original_language'
    )

    list_filter = (
        'release_date',
        'genres',
        'original_language'
    )

    search_fields = ('title', 'overview')

    filter_horizontal = ('genres', 'actors')
