# Generated by Django 2.0.6 on 2018-06-12 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parts', '0034_auto_20180612_1347'),
    ]

    operations = [
        migrations.AlterField(
            model_name='part',
            name='is_equipment',
            field=models.BooleanField(default=False),
        ),
    ]
