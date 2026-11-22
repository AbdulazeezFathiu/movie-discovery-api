
from django.core.management.base import BaseCommand
from movies.tmdb import import_popular_movies


class Command(BaseCommand):
    help = "Import popular movies from TMDB"

    def add_arguments(self, parser):
        parser.add_argument(
            "--pages",
            type=int,
            default=1,
            help="Number of TMDB pages to import"
        )

        parser.add_argument(
            "--force-update",
            action="store_true",
            help="Update movies that already exist"
        )

    def handle(self, *args, **options):
        pages = options["pages"]
        force_update = options["force_update"]

        if pages < 1:
            self.stderr.write(
                self.style.ERROR("--pages must be at least 1")
            )
            return

        self.stdout.write("Starting TMDB movie import...")

        stats = import_popular_movies(
            total_pages=pages,
            force_update=force_update
        )

        self.stdout.write("\n===== IMPORT RESULTS =====")
        self.stdout.write(
            f"Total processed: {stats['total_processed']}"
        )
        self.stdout.write(
            f"Successfully imported: {stats['successful']}"
        )
        self.stdout.write(
            f"Failed imports: {stats['failed']}"
        )
        self.stdout.write(
            f"Skipped: {stats['skipped']}"
        )

        if stats["failed"] > 0:
            self.stdout.write(
                self.style.WARNING(
                    "Import completed with some failures."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Import completed!")
            )
