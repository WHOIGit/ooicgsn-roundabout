# Generated by Django 2.0 on 2018-02-28 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parts', '0016_auto_20180222_1020'),
    ]

    operations = [
        migrations.AddField(
            model_name='part',
            name='friendly_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='part',
            name='name',
            field=models.CharField(max_length=255),
        ),
    ]
