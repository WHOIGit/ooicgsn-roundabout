# Generated by Django 2.2.9 on 2020-04-01 19:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calibrations', '0012_auto_20200401_1853'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='calibrationevent',
            options={'ordering': ['-calibration_date']},
        ),
    ]
