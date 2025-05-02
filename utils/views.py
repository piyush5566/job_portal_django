# utils/views.py
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.contrib import messages
from django.conf import settings
import os
import io
import logging # Import logging
from google.cloud import storage

# Import models from the 'jobs' app
from jobs.models import Application
# Import decorators from auth app
from portal_auth.views import login_required

logger = logging.getLogger(__name__) # Get logger for this module

# --- Views ---

@login_required
def serve_resume_view(request, cs_suffix):
    """
    Securely serve resume files, checking local storage first, then GCS.

    Args:
        cs_suffix (str): The suffix of the GCS object name or local path
                          (e.g., 'user_id/filename.pdf').

    Returns:
        FileResponse: The requested resume file streamed from local disk or GCS.
        HttpResponseForbidden: 403 if unauthorized.
        Http404 Exception: Raised if the file is not found in either location
                           or if GCS is needed but not configured/available.
        500 Error: On unexpected server errors during file access/retrieval.

    Access Rules:
        - Admins: Can access any resume
        - Employers: Can access resumes for their job postings
        - Applicants: Can access their own resumes
    """
    user = request.user
    logger.info(f"Resume access request for path suffix: '{cs_suffix}' by user {user.id} with role {user.role}")

    # Find the application associated with this path suffix.
    # Assumes resume_path stores path suffix like 'user_id/file.pdf'
    application = get_object_or_404(Application.objects.select_related('job', 'applicant'), resume_path=cs_suffix)
    # Note: get_object_or_404 handles the 'not found' case for the application record

    # --- Permission Checks ---
    can_access = False
    if user.is_staff or user.role == 'admin': # Django admin or custom admin
        can_access = True
        logger.info(f"Admin {user.id} accessing resume for application {application.id} (Path suffix: {cs_suffix})")
    elif user.role == 'employer' and application.job.poster == user: # Employer who posted the job
        can_access = True
        logger.info(f"Employer {user.id} accessing resume for application {application.id} (Path suffix: {cs_suffix})")
    elif user == application.applicant: # Applicant accessing their own resume
        can_access = True
        logger.info(f"Applicant {user.id} accessing their own resume for application {application.id} (Path suffix: {cs_suffix})")

    if not can_access:
        logger.warning(f"Unauthorized resume access attempt: User {user.id} for path suffix '{cs_suffix}' (App ID: {application.id})")
        messages.error(request, "You do not have permission to view this resume.")
        return HttpResponseForbidden("Access Denied")
    # --- End Permission Checks ---

    # --- 1. Attempt to Serve Locally First ---
    # Construct the expected absolute local path based on the suffix
    # Assumes resumes are stored under MEDIA_ROOT/resumes/user_id/filename.pdf
    expected_local_path = os.path.join(settings.MEDIA_ROOT, "resumes", cs_suffix)
    logger.debug(f"Checking for local resume file at: {expected_local_path}")

    if os.path.exists(expected_local_path):
        try:
            logger.info(f"Serving resume file '{cs_suffix}' from local storage.")
            # Extract original filename for download prompt
            original_filename = os.path.basename(cs_suffix)
            response = FileResponse(
                open(expected_local_path, 'rb'),
                as_attachment=True,
                filename=original_filename
            )
            return response
        except Exception as e:
            logger.error(f"Error serving local file '{expected_local_path}': {str(e)}")
            # If local file exists but cannot be served, it's a server error
            # Let Django handle this as a 500, or raise a specific 500 exception
            raise # Re-raise the exception to trigger a 500 error

    logger.info(f"Resume file '{cs_suffix}' not found locally. Attempting GCS fetch.")

    # --- 2. If Not Found Locally, Attempt to Fetch from GCS ---
    enable_gcs_setting = getattr(settings, 'ENABLE_GCS_UPLOAD', False)
    gcs_bucket_name = getattr(settings, 'GCS_BUCKET_NAME', None)

    # Check if GCS is configured in settings AND library was imported
    if not enable_gcs_setting or not gcs_bucket_name:
        log_reason = "GCS not enabled or bucket not configured in settings"
        logger.warning(f"Local file '{cs_suffix}' not found and cannot fetch from GCS ({log_reason}). Cannot serve resume.")
        raise Http404("Resume file not found.") # Not found locally, GCS unavailable -> 404

    # --- Proceed with GCS Fetch ---
    try:
        # Construct the full GCS object name (assuming 'resumes/' prefix)
        gcs_object_name = f"resumes/{cs_suffix}"
        logger.info(f"Attempting to serve resume '{gcs_object_name}' from GCS bucket '{gcs_bucket_name}'.")

        storage_client = storage.Client()
        bucket = storage_client.bucket(gcs_bucket_name)
        blob = bucket.blob(gcs_object_name)

        if not blob.exists():
            logger.warning(f"Resume file not found locally or in GCS: {gcs_object_name}")
            raise Http404("Resume file not found.") # Not found in GCS either -> 404

        # Download blob content into memory
        file_bytes = blob.download_as_bytes()
        file_stream = io.BytesIO(file_bytes)

        # Extract original filename for download prompt
        original_filename = os.path.basename(cs_suffix)

        logger.info(f"Resume file {gcs_object_name} successfully retrieved from GCS and serving.")
        # Send the file from the in-memory stream
        response = FileResponse(
            file_stream,
            as_attachment=True,
            filename=original_filename
            # mimetype can be set explicitly if needed, e.g., 'application/pdf'
        )
        return response

    except Exception as e:
        logger.error(f"Error retrieving file '{gcs_object_name}' from GCS after local check failed: {str(e)}")
        # Treat GCS errors as server errors after confirming local absence
        raise Http404("Error serving resume file from storage.") # Or raise e for 500


