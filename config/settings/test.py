from .base import *

# Test settings
DEBUG = False
ALLOWED_HOSTS = ['testserver']

# In-memory database for tests (Django handles test DB creation)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use in-memory email backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Minimal logging during tests
LOGGING['root']['level'] = 'ERROR'