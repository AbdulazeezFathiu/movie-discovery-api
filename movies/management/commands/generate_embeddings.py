
from django.core.management.base import BaseCommand

from movies.models import Movie, MovieEmbedding
from movies.nlp.semantic_search import (
    get_embedding_model,
    MODEL_NAME,
)


class Command(BaseCommand):
    help = "Generate and store movie embeddings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenerate existing embeddings"
        )

    def handle(self, *args, **options):
        force = options["force"]

        movies = Movie.objects.exclude(
            overview=""
        ).exclude(
            overview__isnull=True
        ).order_by("id")

        model = get_embedding_model()

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for movie in movies:
            existing = MovieEmbedding.objects.filter(
                movie=movie
            ).first()

            # Skip embeddings that are already current
            if (
                existing
                and not force
                and existing.model_name == MODEL_NAME
                and existing.source_updated_at == movie.updated_at
            ):
                skipped_count += 1
                continue

            embedding = model.encode_document(
                movie.overview,
                normalize_embeddings=True
            )

            vector = embedding.tolist()

            record, created = MovieEmbedding.objects.update_or_create(
                movie=movie,
                defaults={
                    "vector": vector,
                    "model_name": MODEL_NAME,
                    "source_updated_at": movie.updated_at,
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                "\nEmbedding generation completed!"
            )
        )

        self.stdout.write(
            f"Created: {created_count}"
        )
        self.stdout.write(
            f"Updated: {updated_count}"
        )
        self.stdout.write(
            f"Skipped: {skipped_count}"
        )
