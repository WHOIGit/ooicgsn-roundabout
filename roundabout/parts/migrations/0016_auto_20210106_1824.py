# Generated by Django 3.1.3 on 2021-01-06 18:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parts', '0015_auto_20201116_1949'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='revision',
            options={'get_latest_by': 'created_at', 'ordering': ['-created_at', '-revision_code']},
        ),
    ]
