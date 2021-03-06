# Generated by Django 2.2.10 on 2020-04-24 20:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cruises', '0006_auto_20200424_2051'),
        ('inventory', '0005_auto_20200302_1535'),
    ]

    operations = [
        migrations.AddField(
            model_name='deployment',
            name='cruise_deployed',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deployments', to='cruises.Cruise'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='cruise_recovered',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recovered_deployments', to='cruises.Cruise'),
        ),
    ]
