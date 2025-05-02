# main/urls.py
from django.urls import path
from . import views # Import views from the current directory

app_name = 'main' # Define the namespace for this app's URLs

urlpatterns = [
    # Map the root URL of this app ('') to the index_view
    path('', views.index_view, name='index'),
    # Map '/about/' to the about_view
    path('about/', views.about_view, name='about'),
    # Map '/privacy/' to the privacy_view
    path('privacy/', views.privacy_view, name='privacy'),
    # Map '/terms/' to the terms_view
    path('terms/', views.terms_view, name='terms'),
    # Map '/contact/' to the contact_view
    path('contact/', views.contact_view, name='contact'),
]