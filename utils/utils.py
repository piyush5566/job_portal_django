# utils/utils.py (or a suitable app like 'core/utils.py')

"""
Utility functions for the Django Job Portal application.

This module provides various utility functions used throughout the application:
- File handling (uploads, validation)
- Image processing
- Amazon S3 integration (direct)
- Local/S3 file retrieval helper

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
# AWS_STORAGE_BUCKET_NAME: Name of the S3 bucket (if using S3)
# ENABLE_S3_UPLOAD: Boolean flag to enable S3 uploads

# --- Constants (can also be moved to settings.py) ---
ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
# Paths below are relative to MEDIA_ROOT
PROFILE_UPLOAD_SUBDIR = 'img/profiles'
COMPANY_LOGOS_SUBDIR = 'img/company_logos'
RESUMES_S3_PREFIX = 'resumes/' # Prefix used in S3 object names and local subdirs

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

# --- S3 Upload Function (Using boto3) ---
def upload_to_s3(uploaded_file: UploadedFile, user_id: int, s3_bucket_name: str):
    """
    Uploads a Django UploadedFile directly to Amazon S3.

    Args:
        uploaded_file (UploadedFile): The file object from request.FILES.
        user_id (int): The ID of the user uploading the file.
        s3_bucket_name (str): The name of the target S3 bucket.

    Returns:
        str: The S3 object name (e.g., 'resumes/123/filename.pdf') if successful,
             None otherwise.

    Requires:
        boto3 library installed.
    """
    # Import here to avoid dependency if S3 is not used
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        logger.error("boto3 library not found. Cannot upload to S3.")
        return None

    if not uploaded_file or not s3_bucket_name:
        logger.warning("upload_to_s3: Missing uploaded_file or bucket name.")
        return None

    if not allowed_file(uploaded_file.name, ALLOWED_RESUME_EXTENSIONS):
        logger.warning(f"upload_to_s3: Invalid file type attempted: {uploaded_file.name}")
        return None

    try:
        # Use Django's utility for safer filenames
        filename = get_valid_filename(uploaded_file.name)
        # Construct the object name/path within S3 - place under media/resumes/
        s3_object_name = f"media/{RESUMES_S3_PREFIX}{user_id}/{filename}"

        # Create S3 client
        s3_client = boto3.client('s3')

        # Django's UploadedFile needs to be rewound if read previously
        uploaded_file.seek(0)

        # Upload the file stream directly from the UploadedFile object
        s3_client.upload_fileobj(
            uploaded_file, 
            s3_bucket_name, 
            s3_object_name,
            ExtraArgs={'ContentType': uploaded_file.content_type}
        )

        logger.info(f"Successfully uploaded {filename} to S3 bucket {s3_bucket_name} as {s3_object_name} for user {user_id}")
        return s3_object_name # Return the full S3 path

    except ClientError as e:
        logger.error(f"Error uploading {uploaded_file.name} to S3 for user {user_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error uploading {uploaded_file.name} to S3 for user {user_id}: {str(e)}")
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


# --- Function to get resume file (local or S3) ---
def get_resume_file(resume_path_suffix: str):
    """
    Ensures a resume file exists locally, downloading from S3 if necessary.

    Checks if the file corresponding to `resume_path_suffix` exists in the
    local MEDIA_ROOT. If not found and S3 is enabled, attempts to download
    it from S3 to the expected local path.

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
        Consider streaming responses or using signed URLs for direct S3 access
        in views where possible. This function might be more suitable for
        background tasks or management commands needing local file access.
    """
    if not resume_path_suffix:
        logger.warning("get_resume_file called with empty resume_path_suffix.")
        return None, False

    # Construct the expected absolute local path
    # Assumes resumes are stored under MEDIA_ROOT/resumes/user_id/filename.pdf
    expected_local_path = os.path.join(settings.MEDIA_ROOT, RESUMES_S3_PREFIX, resume_path_suffix)
    logger.debug(f"get_resume_file: Checking for local file at: {expected_local_path}")

    # 1. Check if file exists locally
    if os.path.exists(expected_local_path):
        logger.info(f"get_resume_file: Found resume file locally: {expected_local_path}")
        return expected_local_path, True

    # 2. If not local, check S3 configuration
    logger.info(f"get_resume_file: File not found locally. Checking S3 config.")
    enable_s3 = getattr(settings, 'ENABLE_S3_UPLOAD', False)
    s3_bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)

    if not enable_s3 or not s3_bucket_name:
        logger.warning(f"get_resume_file: Local file missing and S3 is disabled or not configured. Cannot retrieve '{resume_path_suffix}'.")
        return None, False

    # 3. Attempt to download from S3
    try:
        # Import here to avoid dependency if S3 is not used
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        logger.error("boto3 library not found. Cannot download from S3.")
        return None, False

    try:
        # Construct the full S3 object name
        s3_object_name = f"media/{RESUMES_S3_PREFIX}{resume_path_suffix}"
        logger.info(f"get_resume_file: Attempting to download '{s3_object_name}' from S3 bucket '{s3_bucket_name}' to '{expected_local_path}'")

        # Create S3 client
        s3_client = boto3.client('s3')

        # Ensure the local directory exists before downloading
        local_dir = os.path.dirname(expected_local_path)
        os.makedirs(local_dir, exist_ok=True)
        logger.debug(f"get_resume_file: Ensured local directory exists: {local_dir}")

        # Download the file from S3 to the expected local path
        try:
            s3_client.download_file(s3_bucket_name, s3_object_name, expected_local_path)
            logger.info(f"get_resume_file: Successfully downloaded '{s3_object_name}' from S3 to '{expected_local_path}'.")
            return expected_local_path, True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"get_resume_file: File not found in S3 bucket '{s3_bucket_name}' with name '{s3_object_name}'.")
            else:
                logger.error(f"get_resume_file: Error retrieving file '{s3_object_name}' from S3: {str(e)}")
            return None, False

    except Exception as e:
        logger.error(f"get_resume_file: Unexpected error retrieving file from S3: {str(e)}")
        return None, False
