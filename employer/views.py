# employer/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction # For atomic operations if needed
from django.http import Http404
import logging # Import logging

# Import models from the 'jobs' app
from jobs.models import Job, Application
# Import forms from the current app
from .forms import JobForm, ApplicationStatusForm
# Import decorators from auth app
from auth.views import login_required, role_required

logger = logging.getLogger(__name__) # Get logger for this module

# --- Views ---

@login_required
@role_required('employer', 'admin')
def post_job_redirect_view(request):
    """
    Redirects based on role for the 'Post Job' navbar link.
    Equivalent to Flask's post_job_redirect route.
    """
    user = request.user
    if user.role == 'admin':
        logger.info(f"Admin {user.id} redirected from post_job_redirect to admin job creation")
        messages.info(request, 'As an admin, you can create jobs through the admin interface.')
        return redirect('custom_admin:admin_create_job')
    else: # Employer
        logger.info(f"Employer {user.id} redirected from post_job_redirect to new_job form")
        return redirect('employer:new_job')


@login_required
# Corrected: Add 'admin' to the role requirement
@role_required('employer', 'admin')
def new_job_view(request):
    """
    Handle job creation form display and submission for Employers and Admins.
    Equivalent to Flask's new_job route.
    """
    user = request.user
    logger.info(f"New job page accessed by user {user.id} (Role: {user.role})")
    if request.method == 'POST':
        logger.info(f"New job form submitted by user {user.id}")
        # Pass request.FILES for logo upload
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create a Job instance but don't save yet (commit=False)
                job = form.save(commit=False)

                # --- Added: Salary Formatting Logic ---
                salary_data = form.cleaned_data.get('salary')
                if salary_data and not salary_data.startswith('$'):
                    logger.warning(f"Salary format corrected: Prepending '$' to '{salary_data}' for user {user.id}")
                    job.salary = '$' + salary_data
                # If already starts with $ or is empty/None, form.cleaned_data is used implicitly by form.save() later
                # We only override if correction is needed.
                # --- End Added Logic ---

                # Set the poster to the currently logged-in user (works for both employer and admin)
                job.poster = user

                # Log logo processing if file was uploaded
                if 'company_logo' in request.FILES:
                     logger.info(f"Processing company logo upload for new job by user {user.id}: {request.FILES['company_logo'].name}")
                     # Note: Actual saving is handled by job.save() via ModelForm's ImageField

                job.save() # Now save the job with the poster, logo, and potentially corrected salary
                logger.info(f"New job created: ID {job.id} - '{job.title}' at '{job.company}' by user {user.id}")
                messages.success(request, 'Job posted successfully!')

                # Redirect based on role (optional, could always go to employer list or admin list)
                if user.role == 'employer':
                    return redirect('employer:my_jobs')
                else: # Admin
                    return redirect('custom_admin:admin_jobs') # Redirect admin to their job list

            except Exception as e:
                logger.error(f"Error creating job for user {user.id}: {str(e)}")
                messages.error(request, f'An error occurred while posting the job.')
        else:
            logger.warning(f"New job form validation failed for user {user.id}: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        # GET request
        form = JobForm()

    # Decide template based on role? Or use one template?
    # Using employer template for now as Flask version did.
    return render(request, 'employer/new_job.html', {'form': form})


@login_required
@role_required('employer', 'admin') # Only employers view this specific list
def my_jobs_view(request):
    """
    Display jobs posted by the currently logged-in employer.
    Equivalent to Flask's my_jobs route (specifically for employers).
    """
    user = request.user
    logger.info(f"Employer {user.id} accessing their posted jobs ('my_jobs')")
    # Filter jobs by the current user and order by date
    jobs = Job.objects.filter(poster=user).order_by('-posted_date')
    logger.info(f"Found {jobs.count()} jobs posted by employer {user.id}")
    # No need to manually add application_count, use job.applications.count() in template
    return render(request, 'employer/my_jobs.html', {'jobs': jobs})


@login_required
@role_required('employer', 'admin') # Allow admin access too
def job_applications_view(request, job_id):
    """
    Display applications for a specific job owned by the employer or viewed by admin.
    Equivalent to Flask's job_applications route.
    """
    user = request.user
    logger.info(f"User {user.id} (Role: {user.role}) accessing applications for job {job_id}")
    job = get_object_or_404(Job, pk=job_id)

    # Security Check: Ensure user is admin or owns the job
    if user.role == 'employer' and job.poster != user:
        logger.warning(f"Unauthorized access attempt: Employer {user.id} tried to view applications for job {job_id} posted by user {job.poster_id}")
        messages.error(request, 'You do not have permission to view these applications.')
        return redirect('employer:my_jobs')
    # Admins are allowed by role_required decorator

    # Get applications related to this job
    applications = job.applications.select_related('applicant').order_by('-application_date')
    logger.info(f"Found {applications.count()} applications for job {job_id}")

    context = {
        'job': job,
        'applications': applications,
    }
    return render(request, 'employer/job_applications.html', context)


@login_required
@role_required('employer', 'admin') # Allow admin access too
@transaction.atomic # Ensure deletion is all or nothing
def delete_job_view(request, job_id):
    """
    Delete a job posting and its associated applications.
    Handles POST requests only.
    Equivalent to Flask's delete_job route.
    """
    user = request.user
    if request.method != 'POST':
        logger.warning(f"Invalid method {request.method} used for delete_job_view for job {job_id}")
        raise Http404("Method not allowed")

    logger.info(f"Attempting to delete job {job_id} by user {user.id} (Role: {user.role})")
    job = get_object_or_404(Job, pk=job_id)

    # Security Check
    if user.role == 'employer' and job.poster != user:
        logger.warning(f"Unauthorized job deletion attempt: Employer {user.id} tried to delete job {job_id} posted by user {job.poster_id}")
        messages.error(request, 'You do not have permission to delete this job.')
        return redirect('employer:my_jobs')
    # Admins allowed

    try:
        job_title = job.title # Get info before deleting
        job_company = job.company
        # Deletion cascades due to on_delete=models.CASCADE on Application.job
        job.delete()
        logger.info(f"Job {job_id} ('{job_title}' at '{job_company}') and associated applications deleted successfully by user {user.id}")
        messages.success(request, f'Job "{job_title}" and its applications deleted successfully!')
    except Exception as e:
        logger.error(f"Error deleting job {job_id} by user {user.id}: {str(e)}")
        messages.error(request, f'An error occurred while deleting the job.')

    # Redirect based on role
    if user.role == 'employer':
        return redirect('employer:my_jobs')
    else: # Admin
        return redirect('custom_admin:admin_jobs')


@login_required
@role_required('employer', 'admin') # Allow admin access too
def update_application_status_view(request, application_id):
    """
    Update the status of a specific job application. Handles POST requests only.
    Equivalent to Flask's update_application route.
    """
    user = request.user
    if request.method != 'POST':
        logger.warning(f"Invalid method {request.method} used for update_application_status_view for application {application_id}")
        raise Http404("Method not allowed")

    logger.info(f"Attempting to update status for application {application_id} by user {user.id} (Role: {user.role})")
    application = get_object_or_404(Application.objects.select_related('job'), pk=application_id)
    job = application.job

    # Security Check
    if user.role == 'employer' and job.poster != user:
        logger.warning(f"Unauthorized application status update attempt: User {user.id} tried to update application {application_id} for job {job.id} posted by {job.poster_id}")
        messages.error(request, 'You do not have permission to update this application.')
        return redirect('employer:job_applications', job_id=job.id)
    # Admins allowed

    # Use the form to validate the submitted status
    form = ApplicationStatusForm(request.POST)
    if form.is_valid():
        new_status = form.cleaned_data['status']
        previous_status = application.status
        logger.info(f"Updating application {application_id} status from '{previous_status}' to '{new_status}' by user {user.id}")
        try:
            application.status = new_status
            application.save()
            logger.info(f"Application {application_id} status updated successfully to '{new_status}'")
            messages.success(request, f'Application status updated to {application.get_status_display()}.')
        except Exception as e:
            logger.error(f"Failed to update application {application_id} status by user {user.id}: {str(e)}")
            messages.error(request, f'Failed to update application status.')
    else:
        logger.warning(f"Invalid status update attempt for application {application_id} by user {user.id}: {form.errors}")
        messages.error(request, 'Invalid status submitted.')

    # Redirect back to the list of applications for the job (or admin list)
    if user.role == 'employer':
        return redirect('employer:job_applications', job_id=job.id)
    else: # Admin
        return redirect('custom_admin:admin_applications')

