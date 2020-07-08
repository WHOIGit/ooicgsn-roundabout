# Generated by Django 2.2.13 on 2020-06-25 13:24

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('calibrations', '0013_auto_20200623_1851'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='calibrationevent',
            name='user_approver',
        ),
        migrations.AddField(
            model_name='calibrationevent',
            name='user_approver',
            field=models.ManyToManyField(related_name='calibration_events_approver', to=settings.AUTH_USER_MODEL),
        ),
    ]
