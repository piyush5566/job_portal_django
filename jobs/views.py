# jobs/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings # Import Django settings
from django.core.files.storage import FileSystemStorage # Keep for potential fallback/alternative
import os
import logging # Import logging

# Import models (Job, Application) from the current app
from .models import Job, Application
# Import forms from the current app
from .forms import ApplicationForm
# Import decorators from auth app
from portal_auth.views import login_required, role_required
from utils.utils import upload_to_s3 # Import S3 upload utility function
logger = logging.getLogger(__name__) # Setup logger for this module
# --- Views ---

def jobs_list_view(request):
    """
    Display a list of jobs, optionally filtered by GET parameters.
    Equivalent to Flask's jobs_list route.
    """
    location = request.GET.get('location', '').strip()
    category = request.GET.get('category', '').strip()
    company = request.GET.get('company', '').strip()
    logger.info(f"Jobs list page accessed with filters - location: '{location}', category: '{category}', company: '{company}'")

    # Start with all jobs, ordered by most recent
    jobs_query = Job.objects.order_by('-posted_date')

    # Apply filters using case-insensitive contains
    if location:
        jobs_query = jobs_query.filter(location__icontains=location)
    if category:
        jobs_query = jobs_query.filter(category__icontains=category)
    if company:
        jobs_query = jobs_query.filter(company__icontains=company)

    jobs = jobs_query.all() # Execute the query
    logger.info(f"Found {len(jobs)} jobs matching the criteria.")

    context = {
        'jobs': jobs,
        # Pass search terms back for pre-filling the form in the template
        'search_location': location,
        'search_category': category,
        'search_company': company,
    }
    return render(request, 'jobs/list.html', context)


def search_jobs_api_view(request):
    """
    API endpoint for searching jobs (returns JSON).
    Equivalent to Flask's search_jobs route.
    """
    location = request.GET.get('location', '').strip()
    category = request.GET.get('category', '').strip()
    company = request.GET.get('company', '').strip()

    logger.info(f"API search_jobs called with filters - location: '{location}', category: '{category}', company: '{company}'")

    jobs_query = Job.objects.order_by('-posted_date')
    if location:
        jobs_query = jobs_query.filter(location__icontains=location)
    if category:
        jobs_query = jobs_query.filter(category__icontains=category)
    if company:
        jobs_query = jobs_query.filter(company__icontains=company)

    jobs = jobs_query.all()
    logger.info(f"API search_jobs returned {len(jobs)} results")

    # Prepare JSON response data
    jobs_data = [{
        'id': job.id,
        'title': job.title,
        'company': job.company,
        'location': job.location,
        'category': job.category,
        'salary': job.salary,
        # Use .url attribute for ImageField/FileField to get the public URL
        'company_logo_url': job.company_logo.url if job.company_logo else None,
        'posted_date': job.posted_date.isoformat() # ISO format for JS compatibility
    } for job in jobs]

    return JsonResponse({'jobs': jobs_data})


def job_detail_view(request, job_id):
    """
    Display detailed information about a specific job.
    Equivalent to Flask's job_detail route.
    """
    logger.info(f"Job detail page accessed for job_id: {job_id}")
    job = get_object_or_404(Job, pk=job_id)
    has_applied = False
    application_count = None # For admin view

    if request.user.is_authenticated:
        if request.user.role == 'job_seeker':
            # Check if the current user has already applied
            has_applied = Application.objects.filter(job=job, applicant=request.user).exists()
            logger.info(f"User {request.user.id} has {'already applied' if has_applied else 'not applied'} to job {job_id}")
        elif request.user.role == 'admin':
            # Use the efficient count() method on the related manager
            application_count = job.applications.count()
            logger.info(f"Admin {request.user.id} viewing job {job_id} with {application_count} applications")

    context = {
        'job': job,
        'has_applied': has_applied,
        'application_count': application_count, # Will be None if not admin
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
@role_required('job_seeker')
def apply_job_view(request, job_id):
    """
    Handle job application submissions by job seekers, including S3 resume upload.
    Equivalent to Flask's apply_job route.
    """
    job = get_object_or_404(Job, pk=job_id)
    user = request.user
    logger.info(f"Apply job page accessed for job {job_id} by user {user.id}")

    # Check if already applied
    if Application.objects.filter(job=job, applicant=user).exists():
        logger.warning(f"User {user.id} attempted to apply again to job {job_id}, redirecting.")
        messages.warning(request, 'You have already applied to this job.')
        return redirect('jobs:job_detail', job_id=job.id)

    if request.method == 'POST':
        logger.info(f"Application form submitted for job {job_id} by user {user.id}")
        # Pass request.FILES to handle the file upload
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            resume_path_for_db = None # Path to store in DB (without 'resumes/' prefix)
            s3_upload_successful = True # Assume success if no file or S3 disabled

            try:
                # --- Handle Resume Upload ---
                resume_file = form.cleaned_data.get('resume')
                if resume_file:
                    # Check config if S3 should be used
                    # Use getattr for safer access to settings
                    enable_s3 = getattr(settings, 'ENABLE_S3_UPLOAD', False)
                    s3_bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)

                    if enable_s3 and s3_bucket_name:
                        logger.info(f"Attempting S3 upload for application to job {job_id} by user {user.id}")
                        # Attempt direct upload to S3 using the utility function
                        # Assumes upload_to_s3 takes Django's UploadedFile, user ID, bucket name
                        # and returns the full object name like 'resumes/123/file.pdf' or None
                        s3_object_name = upload_to_s3(
                            uploaded_file=resume_file,
                            user_id=user.id,
                            s3_bucket_name=s3_bucket_name
                        )

                        if s3_object_name:
                            # Store S3 path *without* the leading 'media/resumes/' prefix
                            resume_path_for_db = s3_object_name.removeprefix('media/resumes/')
                            logger.info(f"S3 upload successful for job {job_id}, user {user.id}. DB Path: {resume_path_for_db}")
                        else:
                            # S3 upload failed
                            s3_upload_successful = False
                            logger.error(f"S3 upload failed for job {job_id}, user {user.id}")
                            messages.error(request, 'There was an error uploading your resume to cloud storage. Please try again.')
                            # Stay on the page if S3 upload fails
                    else:
                        # S3 not enabled, handle locally (or disallow?)
                        logger.warning(f"Resume provided for job {job_id}, user {user.id}, but S3 upload is disabled or bucket not configured. Resume not saved.")
                        resume_path_for_db = None

                # --- Create Application Record (only if S3 upload was successful or no resume) ---
                if s3_upload_successful:
                    application = Application(
                        job=job,
                        applicant=user,
                        resume_path=resume_path_for_db,
                        status='applied'
                    )
                    application.save()
                    logger.info(f"User {user.id} successfully applied to job {job_id}. Application ID: {application.id}. Resume DB path: {resume_path_for_db}")
                    messages.success(request, 'Your application has been submitted!')
                    return redirect('job_seeker:my_applications')

            except Exception as e:
                # Catch potential DB errors or other unexpected issues
                logger.error(f"Error processing application for job {job_id}, user {user.id}: {str(e)}")
                messages.error(request, 'An unexpected error occurred while submitting your application.')
                # Stay on the page

        else: # Form is not valid
            logger.warning(f"Application form validation failed for job {job_id}, user {user.id}: {form.errors}")
            messages.error(request, 'Please correct the errors in the form.')
            # Stay on the page

    else: # GET request
        form = ApplicationForm()

    # Render the template if GET request or if POST request failed validation/upload
    return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})

