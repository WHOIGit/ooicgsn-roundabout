# Generated by Django 2.2.9 on 2020-03-02 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_auto_20200218_1527'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(choices=[('invadd', 'Add Inventory'), ('invchange', 'Inventory Change'), ('locationchange', 'Location Change'), ('subchange', 'Sub-Assembly Change'), ('addtobuild', 'Add to Build'), ('removefrombuild', 'Remove from Build'), ('deploymentburnin', 'Deployment Burnin'), ('deploymenttosea', 'Deployment to Field'), ('deploymentupdate', 'Deployment Update'), ('deploymentrecover', 'Deployment Recovered'), ('assigndest', 'Assign Destination'), ('removedest', 'Remove Destination'), ('test', 'Test'), ('note', 'Note'), ('historynote', 'Historical Note'), ('ticket', 'Work Ticket'), ('fieldchange', 'Field Change'), ('flag', 'Flag'), ('movetotrash', 'Move to Trash')], max_length=20),
        ),
    ]
