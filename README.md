# Django Email Scheduler with Celery

A Django application to schedule and send emails at specific times using Celery and Redis. The app integrates with the Gmail API for secure email sending via OAuth 2.0.

## Project Structure
```bash
            custom-email-sender/
            │
            ├── custom_email_sender/               # Main Django project directory
            │   ├── __init__.py
            │   ├── settings.py          # Django settings
            │   ├── urls.py              # Project URL configuration
            │   ├── celery.py            # Celery configuration
            │   ├── wsgi.py
            │   └── asgi.py
            │
            ├── esender/                   # Main application directory
            │   ├── __init__.py
            │   ├── models.py            # Email scheduling models
            │   ├── views.py             # Core views for scheduling emails
            │   ├── tasks.py             # Celery tasks for email dispatch
            │   ├── forms.py             # Django form for scheduling emails
            │   ├── urls.py              # App-specific URL configuration
            │   └── templates/
            │       └── esender/ 
                        └── home.html
            │
            ├── static/                  # Static files (CSS, JS, images)
            ├── templates/               # Project-wide templates
            └── manage.py

## Key Features

- **Schedule Emails**: Schedule emails to be sent at a specific date and time.
- **Track Status**: Monitor email statuses (`pending`, `sent`, `failed`).
- **Integrations**: Uses Celery for task scheduling, Redis as a broker, and Gmail API for email sending.

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/django-email-scheduler.git
   cd django-email-scheduler
2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
3. **Configure Gmail API**
   ```bash
   git clone https://github.com/yourusername/django-email-scheduler.git
   cd django-email-scheduler
4. **Apply Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate

## Runing the Application

1. **Start the Celery Worker**
   ```bash
   celery -A myproject worker --loglevel=info

2. **Start Redis**
   ```bash
   redis-server

3. **Start the Django Development Server**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
