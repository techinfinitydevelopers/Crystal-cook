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
from blog.models import Blog


def _truthy(v):
    return str(v).strip().lower() in ("1", "true", "yes", "on")


class Command(BaseCommand):
    help = "Load wp_products + wp_blogs fixtures when empty (or force-replace with FORCE_RESEED=1)."

    def handle(self, *args, **opts):
        force = _truthy(os.environ.get("FORCE_RESEED", ""))
        self._seed(Product, "wp_products", "products", force)
        self._seed(Blog, "wp_blogs", "blog posts", force)

    def _seed(self, Model, fixture, label, force):
        if force:
            n = Model.objects.count()
            Model.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"FORCE_RESEED set — deleted {n} {label}."))
            call_command("loaddata", fixture)
            self.stdout.write(self.style.SUCCESS(f"Reseeded {label}: {Model.objects.count()}."))
            return
        if Model.objects.exists():
            self.stdout.write(f"{label} already present ({Model.objects.count()}); skipping.")
            return
        self.stdout.write(f"No {label} found — loading {fixture}…")
        call_command("loaddata", fixture)
        self.stdout.write(self.style.SUCCESS(f"Loaded {label}: {Model.objects.count()}."))
