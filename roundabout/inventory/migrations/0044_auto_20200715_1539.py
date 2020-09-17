# Generated by Django 2.2.13 on 2020-07-15 15:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('configs_constants', '0010_auto_20200713_1522'),
        ('inventory', '0043_auto_20200709_1404'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='const_default_event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='configs_constants.ConstDefaultEvent'),
        ),
        migrations.AlterField(
            model_name='action',
            name='object_type',
            field=models.CharField(blank=True, choices=[('build', 'Build'), ('inventory', 'Inventory'), ('deployment', 'Deployment'), ('calibrationevent', 'Calibration Event'), ('constantdefaultevent', 'Constant Default Event')], db_index=True, max_length=20),
        ),
    ]
