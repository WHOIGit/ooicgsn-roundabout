# Generated by Django 2.2.13 on 2020-07-08 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calibrations', '0014_auto_20200625_1324'),
    ]

    operations = [
        migrations.AddField(
            model_name='calibrationevent',
            name='detail',
            field=models.TextField(blank=True),
        ),
    ]
