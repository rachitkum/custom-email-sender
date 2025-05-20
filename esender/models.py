from django.db import models

class EmailStatus(models.Model):
    user_email = models.EmailField(unique=True)
    total_sent = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    total_scheduled = models.IntegerField(default=0)
    response_rate = models.FloatField(default=0.0)

    def update_status(self, status):
        if status == 'sent':
            self.total_sent += 1
        elif status == 'failed':
            self.total_failed += 1
        self.save()

    def calculate_response_rate(self):
        total = self.total_sent + self.total_failed
        self.response_rate = (self.total_sent / total * 100) if total > 0 else 0
        self.save()

    def reset(self):
        self.total_sent = 0
        self.total_failed = 0
        self.total_scheduled = 0
        self.response_rate = 0
        self.save()
