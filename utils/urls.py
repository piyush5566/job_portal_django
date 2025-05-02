# /home/gagan/job_portal/job_portal_django/utils/urls.py
from django.urls import path
from . import views

app_name = 'utils'

urlpatterns = [
    # Use re_path for more complex path matching if needed, but path is often sufficient
    path('resume/<path:cs_suffix>/', views.serve_resume_view, name='serve_resume'),
]
