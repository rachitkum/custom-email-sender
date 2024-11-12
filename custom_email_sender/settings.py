from pathlib import Path
import os
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-3)!s_2=_0uijt800ewrdc-1x7-c_6t6%9hpne4xy#8wsz1t5ik'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'esender',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'custom_email_sender.urls'
GOOGLE_CLIENT_ID = '1018808204219-3sbgj6ve3nm06snk4hkvt4giclt2qiae.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
GOOGLE_REDIRECT_URI = 'http://localhost:8000/oauth/google/callback'

# Celery configuration
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
# Remove direct reference to a tasks.py file and adjust schedule to match the task defined directly in your views
CELERY_BEAT_SCHEDULE = {
    'send-scheduled-emails-every-minute': {
        'task': 'esender.tasks.send_email_task',  # Directly reference the task in views
        'schedule': crontab(minute='*/1'),  # Adjust schedule as needed
    },
}
SENDGRID_API_KEY ='Y1geSSFTR8yqnW06HN8-xw'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'custom_email_sender.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
