# salt_and_light/settings/base.py
import os
from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INSTALLED_APPS = [
    # core apps
    'users', 'posts', 'comments', 'prayer_requests', 'files', 'core',
    # third-party
    'corsheaders', 'rest_framework', 'rest_framework.authtoken',
    'dj_rest_auth', 'dj_rest_auth.registration',
    'allauth', 'allauth.account', 'allauth.socialaccount',
    'drf_yasg',
    # built-in
    'django.contrib.sites',
    'django.contrib.staticfiles', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'salt_and_light.urls'
WSGI_APPLICATION = 'salt_and_light.wsgi.application'
AUTH_USER_MODEL = 'users.User'

# Sites framework (required for email verification)
SITE_ID = 1

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'users' / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            
            ],
        },
    },
]
 
# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "users.serializers.CustomTokenObtainPairSerializer",
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = False  # Set to True only for development

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')

# Supabase configuration
SUPABASE_URL = config('SUPABASE_URL', default='')
SUPABASE_KEY = config('SUPABASE_KEY', default='')
SUPABASE_SERVICE_ROLE_KEY = config('SUPABASE_SERVICE_ROLE_KEY', default='')
SUPABASE_POST_IMAGE_BUCKET = config('SUPABASE_POST_IMAGE_BUCKET', default='post-image-storage')

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}
