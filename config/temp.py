# django_job_portal/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-...' # Keep the generated one or replace

DEBUG = True # Set to False for production

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Your apps
    'main',
    'auth', # Contains the User model
    'jobs',
    'employer',
    'job_seeker',
    'admin', # Your custom admin app
    'utils',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Add django-csp middleware if using it for CSP
]

ROOT_URLCONF = 'django_job_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Add top-level templates directory
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True, # Allows Django to find templates in app/templates/ dirs
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth', # Adds 'user' to context
                'django.contrib.messages.context_processors.messages', # Adds 'messages'
                # Add your custom context processors if needed
            ],
        },
    },
]

WSGI_APPLICATION = 'django_job_portal.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        # Or configure PostgreSQL, MySQL, etc.
    }
}

# Password validation (Keep defaults or customize)
AUTH_PASSWORD_VALIDATORS = [ ... ]

# --- Custom User Model ---
# If your User model is in the 'auth' app:
AUTH_USER_MODEL = 'auth.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC' # Or your timezone
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images served directly)
STATIC_URL = 'static/'
# Directory where collectstatic will gather static files for deployment
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Additional directories to find static files (e.g., top-level static dir)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files (User-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' # Where user uploads will be stored locally

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Configuration (Example using console backend for testing)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# For Gmail (less secure, use App Passwords if needed):
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your_email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your_app_password'
DEFAULT_FROM_EMAIL = 'webmaster@localhost' # Or your actual from address
CONTACT_EMAIL_RECIPIENT = 'your_contact_address@example.com' # Your contact form destination

# Login URLs
LOGIN_URL = 'auth:login' # Name of the login URL pattern
LOGIN_REDIRECT_URL = 'main:index' # Where to redirect after successful login if no 'next' param
LOGOUT_REDIRECT_URL = 'main:index' # Where to redirect after logout

# Message Storage (using cookies is common)
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

# Security Settings (Review and uncomment/configure for production)
# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000 # e.g., 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# Content Security Policy (using django-csp or custom middleware)
# CSP_DEFAULT_SRC = ("'self'",)
# CSP_IMG_SRC = ("'self'", 'data:', 'https.cdnjs.cloudflare.com', settings.MEDIA_URL) # Add MEDIA_URL
# ... configure other CSP directives ...

# GCS Settings (if using Google Cloud Storage)
# ENABLE_GCS_UPLOAD = True # Or get from env var
# GCS_BUCKET_NAME = 'your-gcs-bucket-name'
# GCS_PROJECT_ID = 'your-gcp-project-id'
# GOOGLE_APPLICATION_CREDENTIALS = '/path/to/your/service-account-key.json' # Or set env var
# If using django-storages for GCS:
# DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
# GS_BUCKET_NAME = GCS_BUCKET_NAME
# GS_PROJECT_ID = GCS_PROJECT_ID
# GS_CREDENTIALS = ... # Service account object or path
