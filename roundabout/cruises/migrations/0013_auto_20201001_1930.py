# Generated by Django 2.2.13 on 2020-10-01 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cruises', '0012_auto_20200727_1746'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cruise',
            name='cruise_stop_date',
            field=models.DateTimeField(null=True),
        ),
    ]
