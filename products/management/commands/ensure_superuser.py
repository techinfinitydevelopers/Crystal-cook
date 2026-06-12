"""
Create a Django superuser from environment variables, only if it doesn't
already exist. Safe to run on every boot (idempotent), so it works inside
the runtime container where the SQLite volume is mounted.

Env vars:
  DJANGO_SUPERUSER_USERNAME   (required)
  DJANGO_SUPERUSER_PASSWORD   (required)
  DJANGO_SUPERUSER_EMAIL      (optional)
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser from DJANGO_SUPERUSER_* env vars if absent."

    def handle(self, *args, **opts):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

        if not username or not password:
            self.stdout.write("DJANGO_SUPERUSER_USERNAME/PASSWORD not set; skipping superuser.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username, defaults={"email": email}
        )
        if not created:
            self.stdout.write(f"Superuser '{username}' already exists; skipping.")
            return
        user.email = email or user.email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}'."))
