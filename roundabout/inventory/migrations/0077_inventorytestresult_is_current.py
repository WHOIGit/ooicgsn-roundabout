# Generated by Django 3.1.3 on 2022-09-01 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0076_inventorytest_inventorytestresult'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventorytestresult',
            name='is_current',
            field=models.BooleanField(default=False),
        ),
    ]
