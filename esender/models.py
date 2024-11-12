# myapp/models.py
from django.db import models
from django.utils import timezone

class ScheduledEmail(models.Model):
    subject = models.CharField(max_length=255)
    message = models.TextField()
    recipient_email = models.EmailField()
    send_time = models.DateTimeField()
    sent_time = models.DateTimeField(null=True, blank=True)
    status_choices = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='pending')
    
    def __str__(self):
        return f"Email to {self.recipient_email} scheduled for {self.send_time}"
    
    def is_scheduled(self):
        return self.status == 'pending'
    
    def mark_as_sent(self):
        self.status = 'sent'
        self.sent_time = timezone.now()
        self.save()

from django.db import models

class EmailStatus(models.Model):
    total_sent = models.IntegerField(default=0)
    total_pending = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    total_scheduled = models.IntegerField(default=0)
    response_rate = models.FloatField(default=0.0)
    
    def update_status(self, status_type):
        if status_type == 'sent':
            self.total_sent += 1
        elif status_type == 'failed':
            self.total_failed += 1
        elif status_type == 'scheduled':
            self.total_scheduled += 1
        # Add more status types as needed
        self.save()

    def calculate_response_rate(self):
        if self.total_sent + self.total_failed > 0:
            self.response_rate = self.total_sent / (self.total_sent + self.total_failed) * 100
        self.save()

    def __str__(self):
        return f"Total Sent: {self.total_sent}, Failed: {self.total_failed}, Pending: {self.total_pending}"
