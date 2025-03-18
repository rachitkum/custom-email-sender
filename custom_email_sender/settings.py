from pathlib import Path
import os
from dotenv import load_dotenv
from celery.schedules import crontab

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")

# Security
SECRET_KEY = 'django-insecure-3)!s_2=_0uijt800ewrdc-1x7-c_6t6%9hpne4xy#8wsz1t5ik'

DEBUG=True

ALLOWED_HOSTS = ['*']  # Update this for production

# Installed Apps
INSTALLED_APPS = [
    'rest_framework',  # Django REST Framework for APIs
    'esender',         # Your custom app
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'custom_email_sender.urls'

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379")

CELERY_BEAT_SCHEDULE = {
    'send-scheduled-emails-every-minute': {
        'task': 'esender.tasks.send_email_task',
        'schedule': crontab(minute='*/1'),
    },
}

# Google API Settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Authentication
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8081",  # React Native web app in development
    "http://localhost:3000",  # If running from a different port
    "https://custom-email-sender-production.up.railway.app",  # Your production backend URL
]

# If you want to allow all origins temporarily
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
# Localization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static Files (for serving React build files and static assets)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'frontend', 'build', 'static'),  # Include React static files
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Collect static files here during deployment

# React Build Files (for production)
REACT_APP_DIR = os.path.join(BASE_DIR, 'frontend', 'build')
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [REACT_APP_DIR],  # Point to React's build directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI Application
WSGI_APPLICATION = 'custom_email_sender.wsgi.application'

# Default Auto Field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
