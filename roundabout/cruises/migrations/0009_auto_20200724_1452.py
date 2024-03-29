# Generated by Django 2.2.13 on 2020-07-24 14:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cruises', '0008_auto_20200513_1525'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vessel',
            name='IMO_number',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vessel',
            name='MMSI_number',
            field=models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(999999999), django.core.validators.MinValueValidator(100000000)]),
        ),
    ]
