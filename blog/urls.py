from django.urls import path
from .views import blog_list, article_detail

urlpatterns = [
    path('', blog_list, name='blog'),
    path('<slug:slug>/', article_detail, name='article'),
]
