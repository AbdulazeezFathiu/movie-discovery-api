
import requests
from django.conf import settings
from .models import Movie, Genre, Actor, Director


def fetch_popular_movies(page=1):
    url = "https://api.themoviedb.org/3/movie/popular"

    headers = {
        "Authorization": f"Bearer {settings.TMDB_ACCESS_TOKEN}",
        "accept": "application/json"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params={"page": page},
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as error:
        print(f"Error fetching popular movies: {error}")
        return None

def extract_movie_data(movie):

    return {
        "title": movie.get("title"),
        "overview": movie.get("overview"),
        "release_date": movie.get("release_date"),
        "original_language": movie.get("original_language"),
        "poster_url": get_image_url(movie.get("poster_path")),
        "backdrop_url": get_image_url(
            movie.get("backdrop_path"),
            "w500"
        ),
        "rating": movie.get("vote_average"),
        "vote_count": movie.get("vote_count"),
        "tmdb_id": movie.get("id")
    }
def get_image_url(image_path, size="w500"):

    if not image_path:
        return None

    return f"https://image.tmdb.org/t/p/{size}{image_path}"


def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    headers = {
        "Authorization": f"Bearer {settings.TMDB_ACCESS_TOKEN}",
        "accept": "application/json"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as error:
        print(f"Error fetching movie details: {error}")
        return None
def get_or_create_genre(genre_data):

    genre, created = Genre.objects.get_or_create(
        name=genre_data['name']
    )

    return genre
def assign_movie_genres(movie, genre_data):
    genres = []

    for item in genre_data:
        genre = get_or_create_genre(item)
        genres.append(genre)

    movie.genres.set(genres)
def import_movie(tmdb_id, force_update=False):

    existing_movie = Movie.objects.filter(tmdb_id=tmdb_id).first()

    # Skip existing movies unless force_update is True
    if existing_movie and not force_update:
        return existing_movie, False, True

    # Fetch movie details
    details = fetch_movie_details(tmdb_id)

    if details is None:
        return None, False, False

    # Fetch movie credits
    credits = fetch_movie_credits(tmdb_id)

    if credits is None:
        return None, False, False

    movie_data = extract_movie_data(details)

    # Create or update movie
    movie, created = Movie.objects.update_or_create(
        tmdb_id=tmdb_id,
        defaults={
            "title": movie_data.get("title"),
            "overview": movie_data.get("overview") or "",
            "release_date": movie_data.get("release_date") or None,
            "runtime": details.get("runtime") or 0,
            "original_language": movie_data.get("original_language") or "",
            "poster_url": movie_data.get("poster_url") or "",
            "backdrop_url": movie_data.get("backdrop_url") or "",
            "rating": movie_data.get("rating") or 0,
            "vote_count": movie_data.get("vote_count") or 0,
        }
    )

    # Assign relationships
    assign_movie_genres(movie, details.get('genres', []))
    assign_movie_actors(movie, credits.get('cast', []))
    assign_movie_director(movie, credits.get('crew', []))

    return movie, created, False

def import_popular_movies(total_pages=1, force_update=False):

    stats = {
        "total_processed": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "movies": []
    }

    for page in range(1, total_pages + 1):

        data = fetch_popular_movies(page)

        if data is None:
            continue

        for item in data.get('results', []):

            stats["total_processed"] += 1

            tmdb_id = item.get('id')

            if not tmdb_id:
                stats["skipped"] += 1
                continue

            movie, created, skipped = import_movie(
                tmdb_id,
                force_update=force_update
            )

            if skipped:
                stats["skipped"] += 1

            elif movie is None:
                stats["failed"] += 1

            else:
                stats["successful"] += 1
                stats["movies"].append(movie)

    return stats
def fetch_movie_credits(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"

    headers = {
        "Authorization": f"Bearer {settings.TMDB_ACCESS_TOKEN}",
        "accept": "application/json"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as error:
        print(f"Error fetching movie credits: {error}")
        return None
def get_or_create_actor(actor_data):
    actor, created = Actor.objects.get_or_create(
        name=actor_data['name'],
        defaults={
            'profile_url': get_image_url(
                actor_data.get('profile_path')
            ) or ""
        }
    )

    return actor
def assign_movie_actors(movie, cast_data, limit=10):
    movie.actors.clear()

    for item in cast_data[:limit]:
        actor = get_or_create_actor(item)
        movie.actors.add(actor)

def get_or_create_director(crew_data):
    director, created = Director.objects.get_or_create(
        name=crew_data['name'],
        defaults={
            'profile_url': get_image_url(
                crew_data.get('profile_path')
            ) or ""
        }
    )

    return director
def assign_movie_director(movie, crew_data):
    director = None

    for item in crew_data:
        if item.get('job') == 'Director':
            director = get_or_create_director(item)
            break

    movie.director = director
    movie.save()