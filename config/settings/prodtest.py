from .prod import *

# Use a separate test database on the production server
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('TEST_DB_NAME', 'test_' + os.getenv('DB_NAME', '')),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Keep debug off to simulate production
DEBUG = False

# Logging matches production
LOGGING['root']['level'] = 'WARNING'