# admin/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import Http404
import logging # Import logging

# Import models from relevant apps
from portal_auth.models import User
from jobs.models import Job, Application
# Import forms from relevant apps
from portal_auth.forms import AdminRegistrationForm # Assuming UserEditForm is in auth
# Need UserEditForm from auth/forms.py
from portal_admin.forms import UserEditForm
from employer.forms import JobForm, ApplicationStatusForm # JobForm from employer
# Import decorators from auth app
from portal_auth.views import login_required, role_required

logger = logging.getLogger(__name__) # Get logger for this module

# --- Views ---

@login_required
@role_required('admin')
def admin_dashboard_view(request):
    """Render the custom admin dashboard."""
    user = request.user
    logger.info(f"Admin {user.id} accessed the admin dashboard")
    user_count = User.objects.count()
    job_count = Job.objects.count()
    app_count = Application.objects.count()
    context = {
        'user_count': user_count,
        'job_count': job_count,
        'app_count': app_count,
    }
    return render(request, 'admin/dashboard.html', context)


# --- User Management ---

@login_required
@role_required('admin')
def admin_users_view(request):
    """Display all users for admin management."""
    user = request.user
    logger.info(f"Admin {user.id} accessed the users management page")
    users = User.objects.all().order_by('id')
    logger.info(f"Retrieved {users.count()} users for admin view")
    context = {'users': users}
    return render(request, 'admin/users.html', context)


@login_required
@role_required('admin')
def admin_new_user_view(request):
    """Handle creation of new users by admin."""
    admin_user = request.user
    logger.info(f"Admin {admin_user.id} accessed the new user creation page")
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            role = form.cleaned_data['role']
            logger.info(f"Admin {admin_user.id} submitting new user form: Email {email}, Username {username}, Role {role}")
            try:
                if User.objects.filter(email__iexact=email).exists():
                    logger.warning(f"Admin {admin_user.id} user creation failed: Email {email} already exists")
                    messages.error(request, 'An account with this email already exists.')
                else:
                    new_user = User(
                        username=username,
                        email=email,
                        role=role
                    )
                    new_user.set_password(form.cleaned_data['password'])
                    new_user.save()
                    logger.info(f"Admin {admin_user.id} created new user: ID {new_user.id} ({username}, {email}) with role {role}")
                    messages.success(request, f'User "{username}" created successfully.')
                    return redirect('custom_portal_admin:admin_users')
            except Exception as e:
                logger.error(f"Admin {admin_user.id} failed to create user ({email}): {str(e)}")
                messages.error(request, f'Failed to create user.')
        else:
            logger.warning(f"Admin {admin_user.id} new user form validation failed: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminRegistrationForm()
    return render(request, 'admin/new_user.html', {'form': form})


@login_required
@role_required('admin')
def admin_edit_user_view(request, user_id):
    """Handle editing user details as an admin."""
    admin_user = request.user
    logger.info(f"Admin {admin_user.id} accessed edit page for user {user_id}")
    user_to_edit = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        logger.info(f"Admin {admin_user.id} submitting edit form for user {user_id}")
        # Pass instance to the form for update
        form = UserEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            try:
                # Log changes before saving
                old_username = user_to_edit.username
                old_email = user_to_edit.email
                old_role = user_to_edit.role
                new_username = form.cleaned_data['username']
                new_email = form.cleaned_data['email']
                new_role = form.cleaned_data['role']

                updated_user = form.save()
                logger.info(f"Admin {admin_user.id} updated user {user_id}. Changes: username: {old_username}->{new_username}, email: {old_email}->{new_email}, role: {old_role}->{new_role}")
                messages.success(request, f'User "{updated_user.username}" updated successfully.')
                return redirect('custom_portal_admin:admin_users')
            except Exception as e:
                logger.error(f"Admin {admin_user.id} failed to update user {user_id}: {str(e)}")
                messages.error(request, f'Failed to update user.')
        else:
            logger.warning(f"Admin {admin_user.id} edit user form validation failed for user {user_id}: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        # GET request: pre-populate form
        form = UserEditForm(instance=user_to_edit)

    return render(request, 'admin/edit_user.html', {'form': form, 'user_to_edit': user_to_edit})


@login_required
@role_required('admin')
@transaction.atomic
def admin_delete_user_view(request, user_id):
    """Handle user deletion by admin."""
    admin_user = request.user
    if request.method != 'POST':
        logger.warning(f"Invalid method {request.method} used for admin_delete_user_view for user {user_id}")
        raise Http404("Method not allowed")

    logger.info(f"Admin {admin_user.id} attempting to delete user {user_id}")
    user_to_delete = get_object_or_404(User, pk=user_id)

    # Prevent admin from deleting themselves
    if user_to_delete == admin_user:
        logger.warning(f"Admin {admin_user.id} attempted self-deletion (user {user_id}). Denied.")
        messages.error(request, 'You cannot delete your own account.')
        return redirect('custom_portal_admin:admin_users')

    try:
        username = user_to_delete.username
        email = user_to_delete.email
        # Deletion cascades due to model definitions (User -> Job -> Application)
        user_to_delete.delete()
        logger.info(f"Admin {admin_user.id} deleted user {user_id}: {username}, {email}")
        messages.success(request, f'User "{username}" and associated data deleted successfully.')
    except Exception as e:
        logger.error(f"Admin {admin_user.id} failed to delete user {user_id}: {str(e)}")
        messages.error(request, f'Failed to delete user.')

    return redirect('custom_portal_admin:admin_users')


# --- Job Management ---

@login_required
@role_required('admin')
def admin_jobs_view(request):
    """Display all job listings for admin management."""
    admin_user = request.user
    logger.info(f"Admin {admin_user.id} accessed the jobs management page")
    jobs = Job.objects.select_related('poster').order_by('-posted_date')
    logger.info(f"Retrieved {jobs.count()} jobs for admin view")
    context = {'jobs': jobs}
    return render(request, 'admin/jobs.html', context)


@login_required
@role_required('admin')
def admin_create_job_view(request):
    """Handle job creation from admin interface."""
    admin_user = request.user
    logger.info(f"Admin {admin_user.id} accessed create job page")
    if request.method == 'POST':
        logger.info(f"Admin {admin_user.id} submitting create job form")
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                job = form.save(commit=False)
                # Admin creates job, assign poster as the admin user
                job.poster = admin_user
                job.save()
                logger.info(f"Admin {admin_user.id} created new job ID {job.id} ('{job.title}')")
                messages.success(request, f'Job "{job.title}" created successfully.')
                return redirect('custom_portal_admin:admin_jobs')
            except Exception as e:
                logger.error(f"Admin {admin_user.id} failed to create job: {str(e)}")
                messages.error(request, f'Failed to create job.')
        else:
            logger.warning(f"Admin {admin_user.id} create job form validation failed: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        form = JobForm()
    return render(request, 'admin/create_job.html', {'form': form})


@login_required
@role_required('admin')
def admin_edit_job_view(request, job_id):
    """Handle editing job listings as an admin."""
    admin_user = request.user
    logger.info(f"Admin {admin_user.id} accessed edit page for job {job_id}")
    job_to_edit = get_object_or_404(Job, pk=job_id)

    if request.method == 'POST':
        logger.info(f"Admin {admin_user.id} submitting edit form for job {job_id}")
        # Pass instance for update, handle files if JobForm includes them
        form = JobForm(request.POST, request.FILES, instance=job_to_edit)
        if form.is_valid():
            try:
                # Log changes before saving if needed (ModelForms make this slightly harder)
                updated_job = form.save()
                logger.info(f"Admin {admin_user.id} updated job {job_id} ('{updated_job.title}')")
                messages.success(request, f'Job "{updated_job.title}" updated successfully.')
                return redirect('custom_portal_admin:admin_jobs')
            except Exception as e:
                logger.error(f"Admin {admin_user.id} failed to update job {job_id}: {str(e)}")
                messages.error(request, f'Failed to update job.')
        else:
            logger.warning(f"Admin {admin_user.id} edit job form validation failed for job {job_id}: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        # GET request
        form = JobForm(instance=job_to_edit)

    return render(request, 'admin/edit_job.html', {'form': form, 'job': job_to_edit})


@login_required
@role_required('admin')
@transaction.atomic
def admin_delete_job_view(request, job_id):
    """Handle job deletion by admin."""
    admin_user = request.user
    if request.method != 'POST':
        logger.warning(f"Invalid method {request.method} used for admin_delete_job_view for job {job_id}")
        raise Http404("Method not allowed")

    logger.info(f"Admin {admin_user.id} attempting to delete job {job_id}")
    job_to_delete = get_object_or_404(Job, pk=job_id)

    try:
        job_title = job_to_delete.title
        job_company = job_to_delete.company
        # Cascade delete handles applications
        job_to_delete.delete()
        logger.info(f"Admin {admin_user.id} deleted job {job_id} ('{job_title}' at '{job_company}')")
        messages.success(request, f'Job "{job_title}" and its applications deleted successfully.')
    except Exception as e:
        logger.error(f"Admin {admin_user.id} failed to delete job {job_id}: {str(e)}")
        messages.error(request, f'Failed to delete job.')

    return redirect('custom_portal_admin:admin_jobs')


# --- Application Management ---

@login_required
@role_required('admin')
def admin_applications_view(request):
    """Display all job applications for admin management."""
    admin_user = request.user
    logger.info(f"Admin {admin_user.id} accessed the applications management page")
    applications = Application.objects.select_related('job', 'applicant').order_by('-application_date')
    logger.info(f"Retrieved {applications.count()} applications for admin view")
    context = {'applications': applications}
    return render(request, 'admin/applications.html', context)


@login_required
@role_required('admin')
def admin_update_application_view(request, application_id):
    """Update application status as admin."""
    admin_user = request.user
    if request.method != 'POST':
        logger.warning(f"Invalid method {request.method} used for admin_update_application_view for application {application_id}")
        raise Http404("Method not allowed")

    logger.info(f"Admin {admin_user.id} attempting to update status for application {application_id}")
    application = get_object_or_404(Application, pk=application_id)

    # Use the form for validation
    form = ApplicationStatusForm(request.POST)
    if form.is_valid():
        new_status = form.cleaned_data['status']
        previous_status = application.status
        logger.info(f"Admin {admin_user.id} updating application {application_id} status from '{previous_status}' to '{new_status}'")
        try:
            application.status = new_status
            application.save()
            logger.info(f"Application {application_id} status updated successfully to '{new_status}' by admin {admin_user.id}")
            messages.success(request, f'Application status updated to {application.get_status_display()}.')
        except Exception as e:
            logger.error(f"Admin {admin_user.id} failed to update application {application_id} status: {str(e)}")
            messages.error(request, f'Failed to update application status.')
    else:
        logger.warning(f"Admin {admin_user.id} invalid status update attempt for application {application_id}: {form.errors}")
        messages.error(request, 'Invalid status submitted.')

    return redirect('custom_portal_admin:admin_applications')

