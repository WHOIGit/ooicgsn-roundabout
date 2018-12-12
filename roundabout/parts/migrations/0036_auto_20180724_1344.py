# Generated by Django 2.0.6 on 2018-07-24 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parts', '0035_auto_20180612_1352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='part',
            name='name',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='part',
            name='part_number',
            field=models.CharField(db_index=True, max_length=100, unique=True),
        ),
    ]
