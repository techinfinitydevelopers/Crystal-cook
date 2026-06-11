"""
Load the product fixture once, only if the database has no products yet.

Designed to run in the app's *start* command (where the DB / volume is
mounted). It is safe to run on every boot: after the first successful load
it becomes a no-op, so admin edits made later are never clobbered.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = "Load wp_products fixture only when the products table is empty."

    def add_arguments(self, parser):
        parser.add_argument("--fixture", default="wp_products")

    def handle(self, *args, **opts):
        if Product.objects.exists():
            self.stdout.write(f"Products already present ({Product.objects.count()}); skipping seed.")
            return
        self.stdout.write("No products found — loading fixture…")
        call_command("loaddata", opts["fixture"])
        self.stdout.write(self.style.SUCCESS(f"Loaded. Products now: {Product.objects.count()}."))
