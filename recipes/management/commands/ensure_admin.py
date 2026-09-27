import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the first admin login from ADMIN_USERNAME / ADMIN_PASSWORD if it doesn't exist yet."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not username or not password:
            self.stdout.write("ADMIN_USERNAME / ADMIN_PASSWORD not set; skipping.")
            return
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"User '{username}' already exists.")
            return
        User.objects.create_superuser(username=username, email=os.environ.get("ADMIN_EMAIL", ""), password=password)
        self.stdout.write(self.style.SUCCESS(f"Created admin user '{username}'."))
