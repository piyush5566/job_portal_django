# job_seeker/views.py
from django.shortcuts import render
import logging # Import logging

# Import models from the 'jobs' app
from jobs.models import Application
# Import decorators from auth app
from portal_auth.views import login_required, role_required

logger = logging.getLogger(__name__) # Get logger for this module

# --- Views ---

@login_required
@role_required('job_seeker')
def my_applications_view(request):
    """
    Display all job applications submitted by the currently logged-in job seeker.
    Equivalent to Flask's my_applications route.
    """
    user = request.user
    logger.info(f"Job seeker {user.id} accessing their job applications ('my_applications')")
    # Filter applications by the current user, prefetch related job details
    applications = Application.objects.filter(
        applicant=user
    ).select_related('job').order_by('-application_date')

    logger.info(f"Found {applications.count()} applications for job seeker {user.id}")
    return render(request, 'job_seeker/my_applications.html', {'applications': applications})

