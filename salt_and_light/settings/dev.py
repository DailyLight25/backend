# salt_and_light/settings/dev.py
from .base import *
from decouple import config

DEBUG = config('DEBUG', default=True, cast=bool)
SECRET_KEY = config('SECRET_KEY')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

GEMINI_API_KEY = config("GEMINI_API_KEY", default="dummy_key")

LOGGING['root']['level'] = 'DEBUG'