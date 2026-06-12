import json
from django.shortcuts import render, get_object_or_404
from .models import Blog


def _blog_dict(b, request):
    img = request.build_absolute_uri(b.featured_image.url) if b.featured_image else (b.image_url or '')
    return {
        'id': b.id, 'title': b.title, 'slug': b.slug,
        'excerpt': b.excerpt or '',
        'featured_image': img,
        'author': b.author or '',
        'category': b.category.name if b.category else '',
        'published_at': b.published_at.strftime('%Y-%m-%d') if b.published_at else '',
    }


def blog_list(request):
    posts = Blog.objects.filter(is_published=True).select_related('category').order_by('-published_at')
    context = {
        'blogs_json': json.dumps([_blog_dict(b, request) for b in posts]),
    }
    return render(request, 'blog.html', context)


def article_detail(request, slug):
    post = get_object_or_404(Blog.objects.select_related('category'), slug=slug, is_published=True)
    related = Blog.objects.filter(is_published=True).exclude(id=post.id).order_by('-published_at')[:3]
    post_dict = _blog_dict(post, request)
    post_dict['content'] = post.content or ''
    context = {
        'post': post,
        'post_json': json.dumps(post_dict),
        'related_json': json.dumps([_blog_dict(b, request) for b in related]),
    }
    return render(request, 'article.html', context)
