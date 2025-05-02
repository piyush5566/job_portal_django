# /home/gagan/job_portal/job_portal_django/portal_admin/urls.py (Your custom admin section)
from django.urls import path
from . import views # Assuming you create admin/views.py

app_name = 'custom_admin' # Use a distinct namespace

urlpatterns = [
    path('dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('users/', views.admin_users_view, name='admin_users'),
    path('users/new/', views.admin_new_user_view, name='admin_new_user'),
    path('users/<int:user_id>/edit/', views.admin_edit_user_view, name='admin_edit_user'),
    path('users/<int:user_id>/delete/', views.admin_delete_user_view, name='admin_delete_user'),
    path('jobs/', views.admin_jobs_view, name='admin_jobs'),
    path('jobs/new/', views.admin_create_job_view, name='admin_create_job'),
    path('jobs/<int:job_id>/edit/', views.admin_edit_job_view, name='admin_edit_job'),
    path('jobs/<int:job_id>/delete/', views.admin_delete_job_view, name='admin_delete_job'),
    path('applications/', views.admin_applications_view, name='admin_applications'),
    path('applications/<int:application_id>/update/', views.admin_update_application_view, name='admin_update_application'),
]
