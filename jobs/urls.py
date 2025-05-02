# jobs/urls.py
from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('list/', views.jobs_list_view, name='jobs_list'),
    # API endpoint for job search (returns JSON)
    path('search-api/', views.search_jobs_api_view, name='search_jobs_api'),
    path('<int:job_id>/', views.job_detail_view, name='job_detail'),
    path('apply/<int:job_id>/', views.apply_job_view, name='apply_job'),
]
