# Generated by Django 3.1.3 on 2020-11-17 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cruises', '0014_auto_20201002_1827'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vessel',
            name='R2R',
            field=models.BooleanField(blank=True, choices=[(True, 'Yes'), (False, 'No')], null=True),
        ),
        migrations.AlterField(
            model_name='vessel',
            name='active',
            field=models.BooleanField(blank=True, choices=[(True, 'Yes'), (False, 'No')], null=True),
        ),
    ]
