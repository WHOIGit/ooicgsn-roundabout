# Generated by Django 2.0 on 2018-04-03 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parts', '0024_auto_20180329_1339'),
    ]

    operations = [
        migrations.AddField(
            model_name='part',
            name='part_type',
            field=models.CharField(blank=True, choices=[('Cable', 'Cable'), ('Electrical', 'Electrical'), ('Widget', 'Widget')], max_length=50),
        ),
    ]
