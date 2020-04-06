# Generated by Django 2.2.9 on 2020-04-01 18:46

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calibrations', '0010_auto_20200330_1937'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coefficientvalue',
            name='value',
            field=models.CharField(max_length=20, validators=[django.core.validators.RegexValidator(code='numbers_only', message='Numbers only', regex='^([\\s\\d]+)$')]),
        ),
    ]
