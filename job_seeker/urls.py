# job_seeker/urls.py
from django.urls import path
from . import views

app_name = 'job_seeker'

urlpatterns = [
    path('my-applications/', views.my_applications_view, name='my_applications'),
]