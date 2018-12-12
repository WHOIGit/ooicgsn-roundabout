# Generated by Django 2.0 on 2017-12-22 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0004_auto_20171213_1818'),
        ('parts', '0008_auto_20171219_1415'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='part',
            name='location',
        ),
        migrations.AddField(
            model_name='part',
            name='location',
            field=models.ManyToManyField(blank=True, null=True, related_name='parts', to='locations.Location'),
        ),
    ]
