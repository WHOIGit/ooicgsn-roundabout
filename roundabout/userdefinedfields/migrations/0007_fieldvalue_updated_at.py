# Generated by Django 2.2.13 on 2020-08-20 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userdefinedfields', '0006_auto_20200820_1325'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldvalue',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
