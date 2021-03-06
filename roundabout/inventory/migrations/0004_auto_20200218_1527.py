"""
# Copyright (C) 2019-2020 Woods Hole Oceanographic Institution
#
# This file is part of the Roundabout Database project ("RDB" or 
# "ooicgsn-roundabout").
#
# ooicgsn-roundabout is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# ooicgsn-roundabout is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ooicgsn-roundabout in the COPYING.md file at the project root.
# If not, see <http://www.gnu.org/licenses/>.
"""

# Generated by Django 2.2.9 on 2020-02-18 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_auto_20191023_1347'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(choices=[('invadd', 'Add Inventory'), ('invchange', 'Inventory Change'), ('locationchange', 'Location Change'), ('subchange', 'Subassembly Change'), ('addtobuild', 'Add to Build'), ('removefrombuild', 'Remove from Build'), ('deploymentburnin', 'Deployment Burnin'), ('deploymenttosea', 'Deployment to Field'), ('deploymentupdate', 'Deployment Update'), ('deploymentrecover', 'Deployment Recovered'), ('assigndest', 'Assign Destination'), ('removedest', 'Remove Destination'), ('test', 'Test'), ('note', 'Note'), ('historynote', 'Historical Note'), ('ticket', 'Work Ticket'), ('fieldchange', 'Field Change'), ('flag', 'Flag'), ('movetotrash', 'Move to Trash')], max_length=20),
        ),
        migrations.AlterField(
            model_name='deploymentaction',
            name='action_type',
            field=models.CharField(choices=[('deploy', 'Deployed to Field'), ('recover', 'Recovered from Field'), ('retire', 'Retired'), ('create', 'Created'), ('burnin', 'Burn In'), ('details', 'Deployment Details')], max_length=20),
        ),
    ]
