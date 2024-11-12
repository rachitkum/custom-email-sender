
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
# Ensure that it points to your Django project's settings module.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'custom_email_sender.settings')

# Create an instance of the Celery application
app = Celery('custom_email_sender')

# Load the Celery configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover Celery tasks in all registered Django app configs
app.autodiscover_tasks()

# Periodic Task Schedule Configuration
app.conf.beat_schedule = {
    'send-scheduled-emails-every-minute': {
        'task': 'esender.tasks.send_email_task',  # Replace 'your_project_name' with your actual app name
        'schedule': 60.0,  # Every minute (can be modified as per your requirement)
        'args': ('access_token', 'prompt', 'csv_data','rate_limit'),  # Pass static arguments here if required
    },
    # You can add more scheduled tasks if needed
}

# Optional: Debug task to check if Celery is working fine
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


