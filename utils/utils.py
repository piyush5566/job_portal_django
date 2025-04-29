# utils/utils.py (or a suitable app like 'core/utils.py')

"""
Utility functions for the Django Job Portal application.

This module provides various utility functions used throughout the application:
- File handling (uploads, validation)
- Image processing
- Google Cloud Storage integration (direct)
- Local/GCS file retrieval helper

Note: For idiomatic Django file handling, especially with cloud storage,
consider using model FileFields/ImageFields and the django-storages library.
These functions provide direct translation of the original Flask utilities.
"""

import os
import uuid
import logging
from django.conf import settings # Use Django settings
from django.core.files.storage import FileSystemStorage # For local saving examples
from django.core.files.uploadedfile import UploadedFile # Type hint for Django file objects
from django.utils.text import get_valid_filename # Django's way to sanitize filenames

# --- Assumed settings in settings.py ---
# MEDIA_ROOT: Base directory for local media files
# MEDIA_URL: Base URL for media files
# GCS_BUCKET_NAME: Name of the GCS bucket (if using GCS)
# ENABLE_GCS_UPLOAD: Boolean flag to enable GCS uploads

# --- Constants (can also be moved to settings.py) ---
ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
# Paths below are relative to MEDIA_ROOT
PROFILE_UPLOAD_SUBDIR = 'img/profiles'
COMPANY_LOGOS_SUBDIR = 'img/company_logos'
RESUMES_GCS_PREFIX = 'resumes/' # Prefix used in GCS object names and local subdirs

# Logger (uses Django's logging setup configured in settings.py)
logger = logging.getLogger(__name__) # Use __name__ for module-specific logger

# --- Utility functions ---

def allowed_file(filename, allowed_extensions):
    """
    Check if a file has an allowed extension. (No changes needed)

    Args:
        filename (str): The name of the file to check
        allowed_extensions (set): Set of allowed file extensions

    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions

# --- GCS Upload Function (Directly using google-cloud-storage) ---
def upload_to_gcs(uploaded_file: UploadedFile, user_id: int, gcs_bucket_name: str):
    """
    Uploads a Django UploadedFile directly to Google Cloud Storage.

    Args:
        uploaded_file (UploadedFile): The file object from request.FILES.
        user_id (int): The ID of the user uploading the file.
        gcs_bucket_name (str): The name of the target GCS bucket.

    Returns:
        str: The GCS object name (e.g., 'resumes/123/filename.pdf') if successful,
             None otherwise.

    Requires:
        google-cloud-storage library installed.
    """
    # Import here to avoid dependency if GCS is not used
    try:
        from google.cloud import storage
    except ImportError:
        logger.error("google-cloud-storage library not found. Cannot upload to GCS.")
        return None

    if not uploaded_file or not gcs_bucket_name:
        logger.warning("upload_to_gcs: Missing uploaded_file or bucket name.")
        return None

    if not allowed_file(uploaded_file.name, ALLOWED_RESUME_EXTENSIONS):
        logger.warning(f"upload_to_gcs: Invalid file type attempted: {uploaded_file.name}")
        return None

    try:
        # Use Django's utility for safer filenames, though GCS handles many characters
        filename = get_valid_filename(uploaded_file.name)
        # Construct the object name/path within GCS
        gcs_object_name = f"{RESUMES_GCS_PREFIX}{user_id}/{filename}"

        storage_client = storage.Client()
        bucket = storage_client.bucket(gcs_bucket_name)
        blob = bucket.blob(gcs_object_name)

        # Django's UploadedFile needs to be rewound if read previously
        uploaded_file.seek(0)

        # Upload the file stream directly from the UploadedFile object
        blob.upload_from_file(uploaded_file, content_type=uploaded_file.content_type)

        logger.info(f"Successfully uploaded {filename} to GCS bucket {gcs_bucket_name} as {gcs_object_name} for user {user_id}")
        return gcs_object_name # Return the full GCS path

    except Exception as e:
        logger.error(f"Error uploading {uploaded_file.name} to GCS for user {user_id}: {str(e)}")
        # Optionally re-raise or handle specific GCS exceptions
        return None


# --- Local File Saving Functions (Using Django's FileSystemStorage) ---
# Note: These are often unnecessary if using Django's Model ImageField/FileField

def save_company_logo_local(uploaded_file: UploadedFile):
    """
    Save a company logo locally using Django's storage system.

    Generates a UUID-based filename and saves the image relative to MEDIA_ROOT.

    Args:
        uploaded_file (UploadedFile): The company logo file from request.FILES.

    Returns:
        str: The relative path (from MEDIA_ROOT) of the saved logo,
             or None if saving failed or file type invalid.
    """
    if not uploaded_file or not allowed_file(uploaded_file.name, ALLOWED_IMAGE_EXTENSIONS):
        logger.warning(f"Invalid or missing company logo file attempted: {getattr(uploaded_file, 'name', 'N/A')}")
        return None

    try:
        # Get a clean filename and generate a unique name
        filename = get_valid_filename(uploaded_file.name)
        ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4().hex[:16]}{ext}"

        # Define the path relative to MEDIA_ROOT
        save_path = os.path.join(COMPANY_LOGOS_SUBDIR, unique_filename)

        # Use Django's default storage (FileSystemStorage by default)
        fs = FileSystemStorage(location=settings.MEDIA_ROOT) # Specify base location
        actual_filename = fs.save(save_path, uploaded_file) # fs.save returns the actual path saved

        logger.info(f"Company logo saved successfully: {actual_filename}")
        return actual_filename # Return the path relative to MEDIA_ROOT

    except Exception as e:
        logger.error(f"Error saving company logo locally: {str(e)}")
        return None


def save_profile_picture_local(uploaded_file: UploadedFile):
    """
    Save and resize a user profile picture locally using Django's storage.

    Generates a UUID-based filename, saves the image relative to MEDIA_ROOT,
    and resizes it to a standard size (300x300) if it's larger.

    Args:
        uploaded_file (UploadedFile): The profile picture file from request.FILES.

    Returns:
        str: The relative path (from MEDIA_ROOT) to the saved profile picture,
             or the default profile picture path if saving failed or invalid type.
    """
    default_picture_path = os.path.join(PROFILE_UPLOAD_SUBDIR, 'default.jpg') # Relative path

    if not uploaded_file or not allowed_file(uploaded_file.name, ALLOWED_IMAGE_EXTENSIONS):
        logger.warning(f"Invalid or missing profile picture file attempted: {getattr(uploaded_file, 'name', 'N/A')}")
        return default_picture_path

    try:
        # Import Pillow here to avoid dependency if not used
        from PIL import Image
    except ImportError:
        logger.error("Pillow library not found. Cannot resize profile picture.")
        # Decide whether to save without resizing or return default
        return default_picture_path # Or save without resizing

    try:
        # Generate unique filename and path
        filename = get_valid_filename(uploaded_file.name)
        ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4().hex[:16]}{ext}"
        save_path_relative = os.path.join(PROFILE_UPLOAD_SUBDIR, unique_filename)

        # Use Django's storage to save
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        actual_filename_relative = fs.save(save_path_relative, uploaded_file)

        # Get the full path for resizing
        full_picture_path = fs.path(actual_filename_relative)

        # Resize the image
        img = Image.open(full_picture_path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            # Save resized image back to the same path
            # Ensure format is preserved or handled correctly (e.g., convert to JPEG)
            img.save(full_picture_path, format=img.format or 'JPEG', quality=85)
            logger.info(f"Resized profile picture: {actual_filename_relative}")

        logger.info(f"Profile picture saved successfully: {actual_filename_relative}")
        return actual_filename_relative # Return relative path

    except Exception as e:
        logger.error(f"Error saving profile picture locally: {str(e)}")
        return default_picture_path


# --- RE-INTRODUCED: Function to get resume file (local or GCS) ---
def get_resume_file(resume_path_suffix: str):
    """
    Ensures a resume file exists locally, downloading from GCS if necessary.

    Checks if the file corresponding to `resume_path_suffix` exists in the
    local MEDIA_ROOT. If not found and GCS is enabled, attempts to download
    it from GCS to the expected local path.

    Args:
        resume_path_suffix (str): The path suffix as stored in the database,
                                  expected to be like 'user_id/filename.pdf'.

    Returns:
        tuple: (absolute_local_path, success_flag) where absolute_local_path
               is the full path to the file on the local filesystem if found
               or downloaded, or None if not found/retrieved. success_flag is
               a boolean indicating if the file is available locally.

    Note:
        This pattern (downloading to serve) can be inefficient for web requests.
        Consider streaming responses or using signed URLs for direct GCS access
        in views where possible. This function might be more suitable for
        background tasks or management commands needing local file access.
    """
    if not resume_path_suffix:
        logger.warning("get_resume_file called with empty resume_path_suffix.")
        return None, False

    # Construct the expected absolute local path
    # Assumes resumes are stored under MEDIA_ROOT/resumes/user_id/filename.pdf
    expected_local_path = os.path.join(settings.MEDIA_ROOT, RESUMES_GCS_PREFIX, resume_path_suffix)
    logger.debug(f"get_resume_file: Checking for local file at: {expected_local_path}")

    # 1. Check if file exists locally
    if os.path.exists(expected_local_path):
        logger.info(f"get_resume_file: Found resume file locally: {expected_local_path}")
        return expected_local_path, True

    # 2. If not local, check GCS configuration
    logger.info(f"get_resume_file: File not found locally. Checking GCS config.")
    enable_gcs = getattr(settings, 'ENABLE_GCS_UPLOAD', False)
    gcs_bucket_name = getattr(settings, 'GCS_BUCKET_NAME', None)

    if not enable_gcs or not gcs_bucket_name:
        logger.warning(f"get_resume_file: Local file missing and GCS is disabled or not configured. Cannot retrieve '{resume_path_suffix}'.")
        return None, False

    # 3. Attempt to download from GCS
    try:
        # Import here to avoid dependency if GCS is not used
        from google.cloud import storage
    except ImportError:
        logger.error("google-cloud-storage library not found. Cannot download from GCS.")
        return None, False

    try:
        # Construct the full GCS object name
        gcs_object_name = f"{RESUMES_GCS_PREFIX}{resume_path_suffix}"
        logger.info(f"get_resume_file: Attempting to download '{gcs_object_name}' from GCS bucket '{gcs_bucket_name}' to '{expected_local_path}'")

        storage_client = storage.Client()
        bucket = storage_client.bucket(gcs_bucket_name)
        blob = bucket.blob(gcs_object_name)

        if blob.exists():
            # Ensure the local directory exists before downloading
            local_dir = os.path.dirname(expected_local_path)
            os.makedirs(local_dir, exist_ok=True)
            logger.debug(f"get_resume_file: Ensured local directory exists: {local_dir}")

            # Download the file from GCS to the expected local path
            blob.download_to_filename(expected_local_path)
            logger.info(f"get_resume_file: Successfully downloaded '{gcs_object_name}' from GCS to '{expected_local_path}'.")
            return expected_local_path, True
        else:
            logger.warning(f"get_resume_file: File not found in GCS bucket '{gcs_bucket_name}' with name '{gcs_object_name}'.")
            return None, False

    except Exception as e:
        logger.error(f"get_resume_file: Error retrieving file '{gcs_object_name}' from GCS: {str(e)}")
        # Clean up potentially partially downloaded file? Maybe not necessary.
        return None, False
