# Generated by Django 2.2.13 on 2020-09-02 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configs_constants', '0016_auto_20200901_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='configevent',
            name='config_type',
            field=models.CharField(choices=[('cnst', 'Constant'), ('conf', 'Configuration')], default='cnst', max_length=4),
        ),
    ]
