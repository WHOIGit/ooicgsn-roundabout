# Generated by Django 2.2.10 on 2020-05-30 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0031_auto_20200530_0036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deploymentaction',
            name='action_type',
            field=models.CharField(choices=[('startdeployment', 'Start Deployment'), ('deploymentburnin', 'Deployment Burnin'), ('deploymenttofield', 'Deployment to Field'), ('deploymentupdate', 'Deployment Update'), ('deploymentrecover', 'Deployment Recovery'), ('deploymentretire', 'Deployment Retired'), ('deploymentdetails', 'Deployment Details')], max_length=20),
        ),
    ]
