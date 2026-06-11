"""
Load the product fixture into the runtime database.

Runs in the app's *start* command (where the SQLite volume is mounted).

Behaviour:
  • Normal boot: loads the fixture only if the products table is EMPTY,
    so admin edits made later are never clobbered.
  • If env var FORCE_RESEED is truthy: deletes existing products and
    reloads the fixture (use this once to replace stale/demo data, then
    remove the variable so normal boots stop wiping data).
"""
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

from products.models import Product


def _truthy(v):
    return str(v).strip().lower() in ("1", "true", "yes", "on")


class Command(BaseCommand):
    help = "Load wp_products fixture when empty (or force-replace with FORCE_RESEED=1)."

    def add_arguments(self, parser):
        parser.add_argument("--fixture", default="wp_products")

    def handle(self, *args, **opts):
        fixture = opts["fixture"]
        force = _truthy(os.environ.get("FORCE_RESEED", ""))

        if force:
            n = Product.objects.count()
            Product.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"FORCE_RESEED set — deleted {n} existing products."))
            call_command("loaddata", fixture)
            self.stdout.write(self.style.SUCCESS(f"Reseeded. Products now: {Product.objects.count()}."))
            return

        if Product.objects.exists():
            self.stdout.write(f"Products already present ({Product.objects.count()}); skipping seed.")
            return

        self.stdout.write("No products found — loading fixture…")
        call_command("loaddata", fixture)
        self.stdout.write(self.style.SUCCESS(f"Loaded. Products now: {Product.objects.count()}."))
