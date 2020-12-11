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

"""
Auto generate necessary Groups and Permissions for Cruises
Admin - all Permissions
Technician - all permissions
Inventory Only - no permissions
"""

from django.db import migrations, models
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.management import create_permissions

Group = apps.get_model('auth','Group')
Permission = apps.get_model('auth','Permission')

def add_group_permissions(apps, schema_editor):
    # Need to create permissions manually since this is a migration
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    # create Admin group, add all permissions
    group, created = Group.objects.get_or_create(name='admin')
    if created or group:
        # get all models for this app
        content_type = ContentType.objects.filter(app_label='cruises')
        # loop through each model for the app, get the permissions
        for c in content_type:
            permissions = Permission.objects.filter(content_type=c)
            # add permission to group
            for p in permissions:
                group.permissions.add(p)
                group.save()

    # create Technician group, add all permissions
    group, created = Group.objects.get_or_create(name='technician')
    if created or group:
        # get all models for this app
        content_type = ContentType.objects.filter(app_label='cruises')
        # loop through each model for the app, get the permissions
        for c in content_type:
            permissions = Permission.objects.filter(content_type=c)
            # add permission to group
            for p in permissions:
                group.permissions.add(p)
                group.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cruises', '0011_auto_20200724_1539'),
    ]

    operations = [
        migrations.RunPython(add_group_permissions),
    ]
