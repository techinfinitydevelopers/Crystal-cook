"""
Import blog posts from the old Crystal WordPress site (WP REST API).

Source: https://proj.leo9studio.in/projects/crystal-wp/wp-json/wp/v2/posts
Mirrors products/management/commands/import_wp_products.py.

Usage:
    python manage.py import_wp_blogs            # import / update all
    python manage.py import_wp_blogs --purge    # wipe blog posts first
"""
import html
import json
import re
import urllib.request
import urllib.error
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Blog, BlogCategory

BASE = "https://proj.leo9studio.in/projects/crystal-wp/wp-json/wp/v2"
TAG_RE = re.compile(r"<[^>]+>")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "crystal-import/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def clean(text):
    """Unescape entities and strip HTML tags (for titles/excerpts)."""
    return html.unescape(TAG_RE.sub("", text or "")).strip()


def parse_dt(s):
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_default_timezone())
    return dt


class Command(BaseCommand):
    help = "Import blog posts from the old Crystal WordPress site REST API."

    def add_arguments(self, parser):
        parser.add_argument("--purge", action="store_true", help="Delete existing blog posts first.")

    def handle(self, *args, **opts):
        # categories
        cat_by_id = {}
        try:
            for c in fetch(f"{BASE}/categories?per_page=100&_fields=id,name,slug"):
                obj, _ = BlogCategory.objects.update_or_create(
                    slug=c["slug"], defaults={"name": clean(c["name"])}
                )
                cat_by_id[c["id"]] = obj
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Categories fetch failed ({e}); continuing without."))

        if opts["purge"]:
            n = Blog.objects.count()
            Blog.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Purged {n} existing blog posts."))

        created = updated = skipped = 0
        page = 1
        while True:
            url = f"{BASE}/posts?per_page=100&page={page}&_embed=wp:featuredmedia"
            try:
                items = fetch(url)
            except urllib.error.HTTPError as e:
                if e.code == 400:  # past last page
                    break
                raise
            if not items:
                break

            for it in items:
                title = clean((it.get("title") or {}).get("rendered", ""))
                slug = (it.get("slug") or "").strip()
                if not title or not slug:
                    skipped += 1
                    continue

                excerpt = clean((it.get("excerpt") or {}).get("rendered", ""))[:500]
                content = (it.get("content") or {}).get("rendered", "") or ""

                img = ""
                emb = (it.get("_embedded") or {}).get("wp:featuredmedia") or []
                if emb and isinstance(emb, list):
                    img = emb[0].get("source_url") or ""

                cat = None
                for cid in (it.get("categories") or []):
                    if cid in cat_by_id:
                        cat = cat_by_id[cid]
                        break

                _, was_created = Blog.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "title": title,
                        "excerpt": excerpt,
                        "content": content,
                        "image_url": img,
                        "author": "Team Crystal",
                        "category": cat,
                        "is_published": True,
                        "published_at": parse_dt(it.get("date")),
                    },
                )
                created += was_created
                updated += (not was_created)
            page += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created}, updated {updated}, skipped {skipped}. "
            f"Total blog posts now: {Blog.objects.count()}."
        ))
