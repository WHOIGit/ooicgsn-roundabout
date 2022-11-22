# Generated by Django 3.1.3 on 2022-11-21 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0080_inventorytestresult_user'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='inventorytestresult',
            options={'get_latest_by': 'created_at', 'ordering': ['-created_at']},
        ),
        migrations.AlterField(
            model_name='inventorytestresult',
            name='result',
            field=models.CharField(choices=[('pass', 'Pass'), ('fail', 'Fail'), ('pending', 'Pending'), ('unknown', 'Reset to Unknown')], max_length=20),
        ),
    ]
