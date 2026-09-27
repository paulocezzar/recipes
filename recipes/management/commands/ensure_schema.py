from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Create this app's Postgres schema if it doesn't exist (no-op on SQLite)."

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            self.stdout.write("Not Postgres; nothing to do.")
            return
        schema = settings.DB_SCHEMA  # validated in settings: letters, digits, underscores
        with connection.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        self.stdout.write(self.style.SUCCESS(f"Schema '{schema}' is ready."))
