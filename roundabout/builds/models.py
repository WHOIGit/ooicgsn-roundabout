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

import os
import datetime
from datetime import timedelta

from django.db import models
from django.apps import apps
from mptt.models import MPTTModel, TreeForeignKey
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from model_utils import FieldTracker

from roundabout.locations.models import Location
from roundabout.inventory.models import Action, Deployment
from roundabout.assemblies.models import Assembly, AssemblyRevision
from roundabout.users.models import User

# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels
labels = set_app_labels()

# Build model

class Build(models.Model):
    FLAG_TYPES = (
            (True, "Flagged"),
            (False, "Unflagged"),
    )
    build_number = models.CharField(max_length=255, unique=False, db_index=True)
    location = TreeForeignKey(Location, related_name='builds',
                              on_delete=models.SET_NULL, null=True, blank=False)
    assembly = models.ForeignKey(Assembly, related_name='builds',
                             on_delete=models.CASCADE, null=False, db_index=True)
    assembly_revision = models.ForeignKey(AssemblyRevision, related_name='builds',
                             on_delete=models.CASCADE, null=True, db_index=True)
    build_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    detail = models.TextField(blank=True)
    is_deployed = models.BooleanField(default=False)
    # Deprecated in v1.5
    _time_at_sea = models.DurationField(default=timedelta(minutes=0), null=True, blank=True)
    flag = models.BooleanField(choices=FLAG_TYPES, blank=False, default=False)

    tracker = FieldTracker(fields=['location',])

    class Meta:
        ordering = ['assembly_revision', 'build_number']

    def __str__(self):
        return '%s - %s' % (self.assembly_revision.assembly.name, self.build_number)

    @property
    def name(self):
        return self.assembly_revision.assembly.name

    # get all Deployments "time in field", add them up for item's life total
    @property
    def time_at_sea(self):
        deployments = self.deployments.all()
        times = [dep.deployment_time_in_field for dep in deployments]
        total_time_in_field = sum(times, datetime.timedelta())
        return total_time_in_field

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return 'builds'

    def get_actions(self):
        return self.actions.filter(object_type=Action.BUILD)

    def current_deployment(self):
        if self.is_deployed:
            # get the latest deployment if available
            current_deployment = self.deployments.exclude(current_status=Deployment.DEPLOYMENTRETIRE).latest()
            return current_deployment
        return None

    def get_latest_deployment(self):
        try:
            latest_deployment = self.deployments.latest()
            return latest_deployment
        except:
            pass
        return None

    def is_deployed_to_field(self):
        if self.current_deployment():
            if self.current_deployment().current_status == Action.DEPLOYMENTTOFIELD:
                return True
        return False

    def location_changed(self):
        current_location = self.location
        last_location = self.actions.latest().location
        if current_location != last_location:
            return True
        return False


class BuildHyperlink(models.Model):
    text = models.CharField(max_length=255, unique=False, blank=False, null=False)
    url = models.URLField(max_length=1000)
    parent = models.ForeignKey(Build, related_name='hyperlinks',
                 on_delete=models.CASCADE, null=False, blank=False)

    class Meta: ordering = ['text']
    def __str__(self): return self.text


class BuildAction(models.Model):
    BUILDADD = 'buildadd'
    LOCATIONCHANGE = 'locationchange'
    SUBASSEMBLYCHANGE = 'subassemblychange'
    STARTDEPLOYMENT = 'startdeployment'
    REMOVEFROMDEPLOYMENT = 'removefromdeployment'
    DEPLOYMENTBURNIN = 'deploymentburnin'
    DEPLOYMENTTOFIELD = 'deploymenttofield'
    DEPLOYMENTUPDATE = 'deploymentupdate'
    DEPLOYMENTRECOVER = 'deploymentrecover'
    DEPLOYMENTRETIRE = 'deploymentretire'
    DEPLOYMENTDETAILS = 'deploymentdetails'
    TEST = 'test'
    NOTE = 'note'
    HISTORYNOTE = 'historynote'
    TICKET = 'ticket'
    FLAG = 'flag'
    RETIREBUILD = 'retirebuild'
    ACT_TYPES = (
        (BUILDADD, 'Add %s' % (labels['label_builds_app_singular'])),
        (LOCATIONCHANGE, 'Location Change'),
        (SUBASSEMBLYCHANGE, 'Subassembly Change'),
        (STARTDEPLOYMENT, 'Start %s' % (labels['label_deployments_app_singular'])),
        (REMOVEFROMDEPLOYMENT, '%s Ended' % (labels['label_deployments_app_singular'])),
        (DEPLOYMENTBURNIN, '%s Burnin' % (labels['label_deployments_app_singular'])),
        (DEPLOYMENTTOFIELD, '%s to Field' % (labels['label_deployments_app_singular'])),
        (DEPLOYMENTUPDATE, '%s Update' % (labels['label_deployments_app_singular'])),
        (DEPLOYMENTRECOVER, '%s Recovered' % (labels['label_deployments_app_singular'])),
        (DEPLOYMENTRETIRE, '%s Retired' % (labels['label_deployments_app_singular'])),
        (DEPLOYMENTDETAILS, '%s Details Updated' % (labels['label_deployments_app_singular'])),
        (TEST, 'Test'),
        (NOTE, 'Note'),
        (HISTORYNOTE, 'Historical Note'),
        (TICKET, 'Work Ticket'),
        (FLAG, 'Flag'),
        (RETIREBUILD, 'Retire Build'),
    )
    action_type = models.CharField(max_length=20, choices=ACT_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    detail = models.TextField(blank=True)
    user = models.ForeignKey(User, related_name='build_actions',
                             on_delete=models.SET_NULL, null=True, blank=False)
    location = TreeForeignKey(Location, related_name='build_actions',
                              on_delete=models.SET_NULL, null=True, blank=False)
    build = models.ForeignKey(Build, related_name='build_actions',
                                 on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at', 'action_type']
        get_latest_by = 'created_at'

    def __str__(self):
        return self.get_action_type_display()


class PhotoNote(models.Model):
    photo = models.FileField(upload_to='notes/',
                             validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif', 'csv'])])
    build = models.ForeignKey(Build, related_name='build_photos',
                                 on_delete=models.CASCADE, null=True, blank=True)
    action = models.ForeignKey(Action, related_name='build_photos',
                                 on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, related_name='build_photos',
                             on_delete=models.SET_NULL, null=True, blank=False)

    def file_type(self):
        # get the file extension from file name
        name, extension = os.path.splitext(self.photo.name)
        # set the possible extensions for docs and images
        doc_types = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
        image_types = ['.png', '.jpg', '.jpeg', '.gif']

        if extension in doc_types:
            return 'document'
        if extension in image_types:
            return 'image'
        return 'other'


class BuildSnapshot(models.Model):
    build = models.ForeignKey(Build, related_name='build_snapshots', on_delete=models.CASCADE, null=True, blank=True)
    deployment = models.ForeignKey('inventory.Deployment', related_name='build_snapshots',
                                   on_delete=models.SET_NULL, null=True, blank=True)
    deployment_status = models.CharField(max_length=255, null=False, blank=True)
    location = TreeForeignKey(Location, related_name='build_snapshots',
                              on_delete=models.SET_NULL, null=True, blank=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    time_at_sea = models.DurationField(default=timedelta(minutes=0), null=True, blank=True)

    class Meta:
        ordering = ['build', 'deployment', '-created_at']

    def __str__(self):
        return self.build.__str__()


class InventorySnapshot(MPTTModel):
    inventory = models.ForeignKey('inventory.Inventory', related_name='inventory_snapshots',
                                 on_delete=models.SET_NULL, null=True, blank=True)
    parent = TreeForeignKey('self', related_name='children',
                            on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    build = models.ForeignKey(BuildSnapshot, related_name='inventory_snapshots',
                                   on_delete=models.CASCADE, null=True, blank=True)
    location = TreeForeignKey(Location, related_name='inventory_snapshots',
                              on_delete=models.SET_NULL, null=True, blank=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    order = models.CharField(max_length=255, null=False, blank=True, db_index=True)

    class MPTTMeta:
        order_insertion_by = ['order']

    def __str__(self):
        return self.inventory.serial_number
