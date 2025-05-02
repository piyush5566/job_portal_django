# employer/urls.py
from django.urls import path
from . import views

app_name = 'employer'

urlpatterns = [
    # Redirect based on role for the 'Post Job' link
    path('post-job-redirect/', views.post_job_redirect_view, name='post_job_redirect'),
    # Form to create a new job
    path('new/', views.new_job_view, name='new_job'),
    # List of jobs posted by the current employer
    path('my-jobs/', views.my_jobs_view, name='my_jobs'),
    # View applications for a specific job
    path('job/<int:job_id>/applications/', views.job_applications_view, name='job_applications'),
    # Delete a job posting (POST request)
    path('job/<int:job_id>/delete/', views.delete_job_view, name='delete_job'),
    # Update application status (POST request)
    path('application/<int:application_id>/update/', views.update_application_status_view, name='update_application_status'),
]