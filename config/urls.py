from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from products.views import index, all_products, product_detail, brands_page, catalogue_page
from blog.views import blog_list, article_detail
from enquiry.views import enquiry_page, submit_enquiry
from core.views import about, career, privacy, terms, contact

urlpatterns = [
    path('admin/', admin.site.urls),

    # Pages
    path('', index, name='home'),
    path('about/', about, name='about'),
    path('products/', all_products, name='all-products'),
    path('products/<slug:slug>/', product_detail, name='product-detail'),
    path('brands/', brands_page, name='brands'),
    path('catalogue/', catalogue_page, name='catalogue'),
    path('blog/', blog_list, name='blog'),
    path('blog/<slug:slug>/', article_detail, name='article'),
    path('enquiry/', enquiry_page, name='enquiry'),
    path('enquiry/submit/', submit_enquiry, name='enquiry-submit'),
    path('contact/', contact, name='contact'),
    path('career/', career, name='career'),
    path('privacy/', privacy, name='privacy'),
    path('terms/', terms, name='terms'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
