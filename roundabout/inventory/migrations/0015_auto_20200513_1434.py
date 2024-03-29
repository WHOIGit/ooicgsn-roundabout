# Generated by Django 2.2.10 on 2020-05-13 14:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0014_auto_20200512_1452'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='action',
            options={'get_latest_by': 'created_at', 'ordering': ['-created_at', '-id']},
        ),
        migrations.AlterModelOptions(
            name='deployment',
            options={'get_latest_by': 'created_at', 'ordering': ['build', '-created_at']},
        ),
        migrations.AddField(
            model_name='action',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parent_actions', to='inventory.Inventory'),
        ),
    ]
