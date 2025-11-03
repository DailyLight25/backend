# salt_and_light/settings/local.py
from .base import *
from decouple import config

DEBUG = True
SECRET_KEY = config('SECRET_KEY', default='local-secret-key')
ALLOWED_HOSTS = ['*']

# Use SQLite for local dev
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

# Disable email sending
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Dummy Gemini key for local testing
GEMINI_API_KEY = config("GEMINI_API_KEY", default="dummy_key")

# Optional: enable Django debug toolbar or other dev tools
INSTALLED_APPS += [
    # 'debug_toolbar',
]

MIDDLEWARE += [
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
]

LOGGING['root']['level'] = 'ERROR'