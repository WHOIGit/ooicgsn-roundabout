# Generated by Django 2.2.13 on 2020-07-31 14:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('inventory', '0033_auto_20200531_1818'), ('inventory', '0034_auto_20200610_1734'), ('inventory', '0035_auto_20200610_1735'), ('inventory', '0036_auto_20200611_1821'), ('inventory', '0037_auto_20200611_1822'), ('inventory', '0038_auto_20200618_1441'), ('inventory', '0039_auto_20200623_2029')]

    dependencies = [
        ('inventory', '0032_auto_20200530_1349'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(choices=[('invadd', 'Add Inventory'), ('invchange', 'Inventory Change'), ('locationchange', 'Location Change'), ('subchange', 'Sub-Assembly Change'), ('addtobuild', 'Add to Build'), ('removefrombuild', 'Remove from Build'), ('startdeployment', 'Start Deployment'), ('deploymentburnin', 'Deployment Burnin'), ('deploymenttofield', 'Deployment to Field'), ('deploymentupdate', 'Deployment Update'), ('deploymentrecover', 'Deployment Recovery'), ('deploymentretire', 'Deployment Retired'), ('deploymentdetails', 'Deployment Details Updated'), ('assigndest', 'Assign Destination'), ('removedest', 'Remove Destination'), ('test', 'Test'), ('note', 'Note'), ('historynote', 'Historical Note'), ('ticket', 'Work Ticket'), ('fieldchange', 'Field Change'), ('flag', 'Flag'), ('movetotrash', 'Move to Trash')], db_index=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(choices=[('add', 'Added to RDB'), ('locationchange', 'Location Change'), ('subchange', 'Sub-Assembly Change'), ('addtobuild', 'Add to Build'), ('removefrombuild', 'Remove from Build'), ('startdeployment', 'Start Deployment'), ('removefromdeployment', 'Deployment Ended'), ('deploymentburnin', 'Deployment Burnin'), ('deploymenttofield', 'Deployment to Field'), ('deploymentupdate', 'Deployment Update'), ('deploymentrecover', 'Deployment Recovery'), ('deploymentretire', 'Deployment Retired'), ('deploymentdetails', 'Deployment Details Updated'), ('assigndest', 'Assign Destination'), ('removedest', 'Remove Destination'), ('test', 'Test'), ('note', 'Note'), ('historynote', 'Historical Note'), ('ticket', 'Work Ticket'), ('fieldchange', 'Field Change'), ('flag', 'Flag'), ('movetotrash', 'Move to Trash'), ('retirebuild', 'Retire Build')], db_index=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='action',
            name='object_type',
            field=models.CharField(blank=True, choices=[('build', 'Build'), ('inventory', 'Inventory'), ('deployment', 'Deployment')], db_index=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='cruise_deployed',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deployments', to='cruises.Cruise'),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='cruise_recovered',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recovered_deployments', to='cruises.Cruise'),
        ),
        migrations.AlterField(
            model_name='inventorydeployment',
            name='cruise_deployed',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventorydeployments', to='cruises.Cruise'),
        ),
        migrations.AlterField(
            model_name='inventorydeployment',
            name='cruise_recovered',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recovered_inventorydeployments', to='cruises.Cruise'),
        ),
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(choices=[('add', 'Added to RDB'), ('update', 'Details updated'), ('locationchange', 'Location Change'), ('subchange', 'Sub-Assembly Change'), ('addtobuild', 'Add to Build'), ('removefrombuild', 'Remove from Build'), ('startdeployment', 'Start Deployment'), ('removefromdeployment', 'Deployment Ended'), ('deploymentburnin', 'Deployment Burnin'), ('deploymenttofield', 'Deployment to Field'), ('deploymentupdate', 'Deployment Update'), ('deploymentrecover', 'Deployment Recovery'), ('deploymentretire', 'Deployment Retired'), ('deploymentdetails', 'Deployment Details Updated'), ('assigndest', 'Assign Destination'), ('removedest', 'Remove Destination'), ('test', 'Test'), ('note', 'Note'), ('historynote', 'Historical Note'), ('ticket', 'Work Ticket'), ('fieldchange', 'Field Change'), ('flag', 'Flag'), ('movetotrash', 'Move to Trash'), ('retirebuild', 'Retire Build')], db_index=True, max_length=20),
        ),
    ]
