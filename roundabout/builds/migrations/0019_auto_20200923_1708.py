# Generated by Django 2.2.13 on 2020-09-23 17:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builds', '0018_auto_20200617_2055'),
    ]

    operations = [
        migrations.RenameField(
            model_name='build',
            old_name='time_at_sea',
            new_name='_time_at_sea',
        ),
    ]
