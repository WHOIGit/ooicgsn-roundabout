# Generated by Django 2.2.13 on 2020-09-01 17:04

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calibrations', '0018_auto_20200812_1515'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calibrationevent',
            name='user_draft',
            field=models.ManyToManyField(blank=True, related_name='calibration_events_drafter', to=settings.AUTH_USER_MODEL),
        ),
    ]