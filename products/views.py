import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Brand, Category, Product, Marketplace


def _resolve_url(url):
    """Relative seed paths (e.g. 'about-assets/x.jpg') live under static/."""
    if not url:
        return ''
    if url.startswith('http://') or url.startswith('https://') or url.startswith('/'):
        return url
    return settings.STATIC_URL + url


def _brand_dict(b, request):
    logo_url = request.build_absolute_uri(b.logo.url) if b.logo else ''
    cat_url = request.build_absolute_uri(b.catalogue.url) if b.catalogue else ''
    return {
        'id': b.id, 'name': b.name, 'slug': b.slug,
        'tagline': b.tagline, 'description': b.description,
        'logo': logo_url, 'catalogue_url': cat_url,
    }


def _cat_dict(c):
    return {
        'id': c.id, 'name': c.name, 'slug': c.slug,
        'parent': c.parent.slug if c.parent else None,
        'parent_name': c.parent.name if c.parent else None,
        'order': c.order,
    }


def _product_dict(p, request):
    img_url = ''
    if p.featured_image:
        img_url = request.build_absolute_uri(p.featured_image.url)
    elif p.image_url:
        img_url = _resolve_url(p.image_url)

    thumb_url = ''
    if p.thumbnail:
        thumb_url = request.build_absolute_uri(p.thumbnail.url)

    return {
        'id': p.id, 'name': p.name, 'slug': p.slug, 'sku': p.sku or '',
        'brand': p.brand.slug if p.brand else '',
        'brand_name': p.brand.name if p.brand else '',
        'category': p.category.slug if p.category else '',
        'category_name': p.category.name if p.category else '',
        'short_description': p.short_description or '',
        'highlight': p.highlight or '',
        'collection_name': p.collection_name or '',
        'tags': p.tags or [],
        'image_url': img_url,
        'thumbnail': thumb_url,
        'is_featured': p.is_featured,
        'is_new': p.is_new,
    }


def _product_detail_dict(p, request):
    d = _product_dict(p, request)
    d['overview'] = p.overview or ''
    d['images'] = [
        request.build_absolute_uri(i.image.url) for i in p.images.all() if i.image
    ]
    d['specifications'] = [
        {'key': s.key, 'value': s.value} for s in p.specifications.all()
    ]
    d['variants'] = [v.name for v in p.variants.all()]
    d['marketplace_links'] = [
        {
            'name': ml.marketplace.name,
            'slug': ml.marketplace.slug,
            'url': ml.url,
            'logo': request.build_absolute_uri(ml.marketplace.logo.url) if ml.marketplace.logo else '',
        }
        for ml in p.marketplace_links.select_related('marketplace').all()
    ]
    return d


def index(request):
    brands = Brand.objects.filter(is_active=True)
    featured = Product.objects.filter(is_active=True, is_featured=True).select_related('brand', 'category')[:12]
    new_arrivals = Product.objects.filter(is_active=True, is_new=True).select_related('brand', 'category')[:6]
    categories = Category.objects.filter(parent=None)

    context = {
        'brands_json': json.dumps([_brand_dict(b, request) for b in brands]),
        'featured_json': json.dumps([_product_dict(p, request) for p in featured]),
        'new_arrivals_json': json.dumps([_product_dict(p, request) for p in new_arrivals]),
        'categories_json': json.dumps([_cat_dict(c) for c in categories]),
    }
    return render(request, 'index.html', context)


def all_products(request):
    products = Product.objects.filter(is_active=True).select_related('brand', 'category')
    brands = Brand.objects.filter(is_active=True)
    categories = Category.objects.all()

    context = {
        'products_json': json.dumps([_product_dict(p, request) for p in products]),
        'brands_json': json.dumps([_brand_dict(b, request) for b in brands]),
        'categories_json': json.dumps([_cat_dict(c) for c in categories]),
    }
    return render(request, 'all-products.html', context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('brand', 'category').prefetch_related(
            'images', 'specifications', 'variants', 'marketplace_links__marketplace'
        ),
        slug=slug, is_active=True
    )
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id).select_related('brand', 'category')[:4]

    context = {
        'product_json': json.dumps(_product_detail_dict(product, request)),
        'related_json': json.dumps([_product_dict(p, request) for p in related]),
        'product': product,
    }
    return render(request, 'product.html', context)


def brands_page(request):
    brands = Brand.objects.filter(is_active=True)
    context = {
        'brands_json': json.dumps([_brand_dict(b, request) for b in brands]),
    }
    return render(request, 'brands.html', context)


def catalogue_page(request):
    brands = Brand.objects.filter(is_active=True)
    context = {
        'brands_json': json.dumps([_brand_dict(b, request) for b in brands]),
    }
    return render(request, 'catalogue.html', context)
