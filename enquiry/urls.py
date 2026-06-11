from django.urls import path
from .views import enquiry_page, submit_enquiry

urlpatterns = [
    path('', enquiry_page, name='enquiry'),
    path('submit/', submit_enquiry, name='enquiry-submit'),
]
