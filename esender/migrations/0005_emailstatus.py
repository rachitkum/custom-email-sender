# Generated by Django 5.0.3 on 2024-11-10 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('esender', '0004_remove_scheduledemail_email_batch_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_sent', models.IntegerField(default=0)),
                ('total_pending', models.IntegerField(default=0)),
                ('total_failed', models.IntegerField(default=0)),
                ('total_scheduled', models.IntegerField(default=0)),
                ('response_rate', models.FloatField(default=0.0)),
            ],
        ),
    ]
