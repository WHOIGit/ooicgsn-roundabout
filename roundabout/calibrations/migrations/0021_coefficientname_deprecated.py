# Generated by Django 2.2.13 on 2020-09-08 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calibrations', '0020_auto_20200901_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='coefficientname',
            name='deprecated',
            field=models.BooleanField(default=False),
        ),
    ]
