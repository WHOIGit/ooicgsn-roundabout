# Generated by Django 2.0 on 2017-12-22 17:04

from django.db import migrations
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('parts', '0009_auto_20171222_1152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='part',
            name='location',
            field=mptt.fields.TreeManyToManyField(blank=True, null=True, related_name='parts', to='locations.Location'),
        ),
    ]
