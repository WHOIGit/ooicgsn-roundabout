# Generated by Django 2.2.13 on 2020-07-24 14:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calibrations', '0016_auto_20200720_1902'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='calibrationevent',
            options={'get_latest_by': 'calibration_date', 'ordering': ['-calibration_date']},
        ),
    ]
