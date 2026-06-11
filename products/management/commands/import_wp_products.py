"""
Import product catalogue data from the old Crystal WordPress site.

Source: https://proj.leo9studio.in/projects/crystal-wp/  (WP REST API)
Pulls the `product` custom post type + `product-category`, `product-type`
(brand) and `size` taxonomies, and maps them onto our Django models.

Usage:
    python manage.py import_wp_products              # import / update all
    python manage.py import_wp_products --limit 20   # first 20 (testing)
    python manage.py import_wp_products --purge       # wipe products first
"""
import json
import html
import urllib.request
import urllib.error

from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Brand, Category, Product, ProductVariant

BASE = "https://proj.leo9studio.in/projects/crystal-wp/wp-json/wp/v2"

# Old WP top-level slugs -> the slugs this site's category pages expect.
PARENT_SLUG_MAP = {
    "electric-appliances": "appliances",
    "cleaning-aid": "cleaning",
}

# product-type taxonomy = brand
BRAND_DEFS = {
    "crystal": ("Crystal", "World of Kitchenware"),
    "crystalina": ("Crystalina", "Splendid Finish"),
    "sparkmate": ("SparkMate", "Cleaning Simplified"),
    "valmate": ("ValMate", "Value for Money"),
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "crystal-import/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def clean(text):
    return html.unescape(text or "").strip()


class Command(BaseCommand):
    help = "Import products from the old Crystal WordPress site REST API."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Max products (0 = all).")
        parser.add_argument("--purge", action="store_true", help="Delete existing products first.")

    def handle(self, *args, **opts):
        limit = opts["limit"]

        # ---- 1. Categories -------------------------------------------------
        self.stdout.write("Fetching categories…")
        terms = fetch(f"{BASE}/product-category?per_page=100&_fields=id,slug,name,parent")
        id2term = {t["id"]: t for t in terms}

        def site_slug(t):
            return PARENT_SLUG_MAP.get(t["slug"], t["slug"])

        cat_objs = {}  # wp term id -> Category
        # parents first (parent == 0), then children, so FK is available
        for t in sorted(terms, key=lambda x: x["parent"]):
            parent_obj = cat_objs.get(t["parent"]) if t["parent"] else None
            obj, _ = Category.objects.update_or_create(
                slug=site_slug(t),
                defaults={"name": clean(t["name"]), "parent": parent_obj},
            )
            cat_objs[t["id"]] = obj
        self.stdout.write(f"  {len(cat_objs)} categories ready.")

        # fallback category for products with no category term
        fallback_cat, _ = Category.objects.update_or_create(
            slug="others", defaults={"name": "Others", "parent": None}
        )

        # ---- 2. Brands -----------------------------------------------------
        for slug, (name, tag) in BRAND_DEFS.items():
            Brand.objects.update_or_create(
                slug=slug, defaults={"name": name, "tagline": tag, "is_active": True}
            )
        default_brand = Brand.objects.get(slug="crystal")
        type2brand = {}
        for t in fetch(f"{BASE}/product-type?per_page=100&_fields=id,slug,name"):
            b = Brand.objects.filter(slug=t["slug"]).first()
            if b:
                type2brand[t["id"]] = b

        # ---- 3. Sizes (variant labels) ------------------------------------
        size_map = {}
        try:
            for s in fetch(f"{BASE}/size?per_page=100&_fields=id,name"):
                size_map[s["id"]] = clean(s["name"])
        except Exception:
            pass

        if opts["purge"]:
            n = Product.objects.count()
            Product.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Purged {n} existing products."))

        # ---- 4. Products ---------------------------------------------------
        self.stdout.write("Fetching products…")
        created = updated = skipped = 0
        page = 1
        done = False
        while not done:
            url = f"{BASE}/product?per_page=100&page={page}&_embed=wp:featuredmedia"
            try:
                items = fetch(url)
            except urllib.error.HTTPError as e:
                if e.code == 400:  # past last page
                    break
                raise
            if not items:
                break

            for it in items:
                name = clean((it.get("title") or {}).get("rendered", ""))
                slug = (it.get("slug") or "").strip()
                if not name or not slug:
                    skipped += 1
                    continue

                # category: prefer a child (parent != 0), else first, else fallback
                cids = it.get("product-category") or []
                chosen = next((c for c in cids if id2term.get(c, {}).get("parent")), None)
                if chosen is None and cids:
                    chosen = cids[0]
                category = cat_objs.get(chosen, fallback_cat)

                # brand from product-type
                brand = default_brand
                for tid in (it.get("product-type") or []):
                    if tid in type2brand:
                        brand = type2brand[tid]
                        break

                # featured image url (embedded)
                img = ""
                emb = (it.get("_embedded") or {}).get("wp:featuredmedia") or []
                if emb and isinstance(emb, list):
                    img = emb[0].get("source_url") or ""

                obj, was_created = Product.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "name": name,
                        "brand": brand,
                        "category": category,
                        "image_url": img,
                        "is_active": True,
                    },
                )
                created += was_created
                updated += (not was_created)

                # size variants
                sizes = [size_map[s] for s in (it.get("size") or []) if s in size_map]
                if sizes:
                    obj.variants.all().delete()
                    for i, sname in enumerate(sizes):
                        ProductVariant.objects.create(
                            product=obj, name=sname, is_default=(i == 0), order=i
                        )

                if limit and (created + updated) >= limit:
                    done = True
                    break
            page += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created}, updated {updated}, skipped {skipped}. "
            f"Total products now: {Product.objects.count()}."
        ))
