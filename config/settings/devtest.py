from .dev import *

# Override database to avoid conflicts with development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'devtest.db',
    }
}

# Ensure debug is enabled
DEBUG = True

# Logging with debug output
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
}