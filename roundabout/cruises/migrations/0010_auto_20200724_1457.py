# Generated by Django 2.2.13 on 2020-07-24 14:57

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cruises', '0009_auto_20200724_1452'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vessel',
            name='length',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]),
        ),
        migrations.AlterField(
            model_name='vessel',
            name='max_draft',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]),
        ),
        migrations.AlterField(
            model_name='vessel',
            name='max_speed',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]),
        ),
    ]
