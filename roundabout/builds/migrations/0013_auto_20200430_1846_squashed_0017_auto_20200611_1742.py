# Generated by Django 2.2.13 on 2020-07-31 14:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    replaces = [('builds', '0013_auto_20200430_1846'), ('builds', '0014_auto_20200523_1926'), ('builds', '0015_auto_20200527_1430'), ('builds', '0016_auto_20200531_1905'), ('builds', '0017_auto_20200611_1742')]

    dependencies = [
        ('builds', '0012_auto_20200427_2056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='buildaction',
            name='build',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='build_actions', to='builds.Build'),
        ),
        migrations.AlterField(
            model_name='buildaction',
            name='location',
            field=mptt.fields.TreeForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='build_actions', to='locations.Location'),
        ),
        migrations.AlterField(
            model_name='buildaction',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='build_actions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='buildaction',
            name='action_type',
            field=models.CharField(choices=[('buildadd', 'Add Build'), ('locationchange', 'Location Change'), ('subassemblychange', 'Subassembly Change'), ('startdeploy', 'Start Deployment'), ('removefromdeployment', 'Deployment Ended'), ('deploymentburnin', 'Deployment Burnin'), ('deploymenttosea', 'Deployment to Field'), ('deploymentupdate', 'Deployment Update'), ('deploymentrecover', 'Deployment Recovered'), ('deploymentdetails', 'Deployment Details Updated'), ('test', 'Test'), ('note', 'Note'), ('historynote', 'Historical Note'), ('ticket', 'Work Ticket'), ('flag', 'Flag'), ('retirebuild', 'Retire Build')], max_length=20),
        ),
        migrations.AlterField(
            model_name='buildaction',
            name='action_type',
            field=models.CharField(choices=[('buildadd', 'Add Build'), ('locationchange', 'Location Change'), ('subassemblychange', 'Subassembly Change'), ('startdeploy', 'Start Deployment'), ('removefromdeployment', 'Deployment Ended'), ('deploymentburnin', 'Deployment Burnin'), ('deploymenttosea', 'Deployment to Field'), ('deploymentupdate', 'Deployment Update'), ('deploymentrecover', 'Deployment Recovered'), ('deploymentretire', 'Deployment Retired'), ('deploymentdetails', 'Deployment Details Updated'), ('test', 'Test'), ('note', 'Note'), ('historynote', 'Historical Note'), ('ticket', 'Work Ticket'), ('flag', 'Flag'), ('retirebuild', 'Retire Build')], max_length=20),
        ),
        migrations.AlterField(
            model_name='buildaction',
            name='action_type',
            field=models.CharField(choices=[('buildadd', 'Add Build'), ('locationchange', 'Location Change'), ('subassemblychange', 'Subassembly Change'), ('startdeployment', 'Start Deployment'), ('removefromdeployment', 'Deployment Ended'), ('deploymentburnin', 'Deployment Burnin'), ('deploymenttofield', 'Deployment to Field'), ('deploymentupdate', 'Deployment Update'), ('deploymentrecover', 'Deployment Recovered'), ('deploymentretire', 'Deployment Retired'), ('deploymentdetails', 'Deployment Details Updated'), ('test', 'Test'), ('note', 'Note'), ('historynote', 'Historical Note'), ('ticket', 'Work Ticket'), ('flag', 'Flag'), ('retirebuild', 'Retire Build')], max_length=20),
        ),
    ]
