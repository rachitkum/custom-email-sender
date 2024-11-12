from __future__ import absolute_import, unicode_literals

# from ..custom_email_sender.celery import app as celery_app
from .celery import app as celery_app
__all__ = ('celery_app',)
