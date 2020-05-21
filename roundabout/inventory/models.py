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
from django.contrib.postgres.fields import JSONField
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator, FileExtensionValidator
from model_utils import FieldTracker
from mptt.models import MPTTModel, TreeForeignKey

from roundabout.locations.models import Location
from roundabout.parts.models import Part, Revision
from roundabout.assemblies.models import Assembly, AssemblyPart
from roundabout.builds.models import Build
from roundabout.cruises.models import Cruise
from roundabout.users.models import User
# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels
labels = set_app_labels()
# Model Managers


# Inventory/Deployment models

class Deployment(models.Model):
    deployment_number = models.CharField(max_length=255, unique=False)
    location = TreeForeignKey(Location, related_name='deployments',
                              on_delete=models.SET_NULL, null=True, blank=True)
    final_location = TreeForeignKey(Location, related_name='final_deployments',
                              on_delete=models.SET_NULL, null=True, blank=True)
    deployed_location = TreeForeignKey(Location, related_name='deployed_deployments',
                              on_delete=models.SET_NULL, null=True, blank=True)
    assembly = models.ForeignKey(Assembly, related_name='deployments',
                             on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    build = models.ForeignKey(Build, related_name='deployments',
                             on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    cruise_deployed = models.ForeignKey(Cruise, related_name='deployments',
                             on_delete=models.SET_NULL, null=True, blank=True)
    cruise_recovered = models.ForeignKey(Cruise, related_name='recovered_deployments',
                                 on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['build', '-created_at']
        get_latest_by = 'created_at'

    def __str__(self):
        if self.deployed_location:
            return '%s - %s' % (self.deployment_number, self.deployed_location)
        return '%s - %s' % (self.deployment_number, self.location.name)

    def get_deployment_label(self):
        return self.deployment_number

    def current_deployment_status(self):
        deployment_action = self.deployment_actions.latest()
        if deployment_action:
            if deployment_action.action_type == 'details':
                deployment_status = 'deploy'
            else:
                deployment_status = deployment_action.action_type
        else:
            deployment_status = 'create'

        return deployment_status

    def get_deploytosea_details(self):
        deploytosea_details = None
        # get the latest 'Deploy' action record to initial
        deploy_record = DeploymentAction.objects.filter(deployment=self).filter(action_type='deploy').first()
        # get the latest 'Detail' action record to find last lat/long/depth data
        action_record = DeploymentAction.objects.filter(deployment=self).filter(action_type='details').first()

        if action_record:
            # create dictionary of location details
            deploytosea_details = {
                'latitude':  action_record.latitude,
                'longitude': action_record.longitude,
                'depth': action_record.depth,
                'deploy_date': deploy_record.created_at,
            }

        return deploytosea_details

    # get the time delta from Deployment start to retire
    def get_deployment_time_total(self):
        try:
            action_deploy_start = DeploymentAction.objects.filter(deployment=self).filter(action_type='create').latest('created_at')
        except DeploymentAction.DoesNotExist:
            action_deploy_to_sea = None

        try:
            action_deploy_retire = DeploymentAction.objects.filter(deployment=self).filter(action_type='retire').latest('created_at')
        except DeploymentAction.DoesNotExist:
            action_deploy_retire = None

        if action_deploy_start:
            if action_deploy_retire:
                deployment_time_total = action_deploy_retire.created_at - action_deploy_start.created_at
                return deployment_time_total
            # If no recovery, item is still at sea
            now = timezone.now()
            time_on_deployment = now - action_deploy_start.created_at
            return deployment_time_total
        return timedelta(minutes=0)

    # get the most recent Deploy to Sea and Recover from Sea action timestamps, find time delta for Total Time at sea
    def get_deployment_time_at_sea(self):
        try:
            action_deploy_to_sea = DeploymentAction.objects.filter(deployment=self).filter(action_type='deploy').latest('created_at')
        except DeploymentAction.DoesNotExist:
            action_deploy_to_sea = None

        try:
            action_recover = DeploymentAction.objects.filter(deployment=self).filter(action_type='recover').latest('created_at')
        except DeploymentAction.DoesNotExist:
            action_recover = None

        if action_deploy_to_sea:
            if action_recover:
                deployment_time_at_sea = action_recover.created_at - action_deploy_to_sea.created_at
                return deployment_time_at_sea
            # If no recovery, item is still at sea
            now = timezone.now()
            deployment_time_at_sea = now - action_deploy_to_sea.created_at
            return deployment_time_at_sea
        return timedelta(minutes=0)

    def get_deployment_status_label(self):
        deployment_status_label = None
        # get short label text for Deployment status
        if self.current_deployment_status() == 'create':
            deployment_status_label = 'Initial %s' % (labels['label_deployments_app_singular'])
        elif self.current_deployment_status() == 'burnin':
            deployment_status_label = 'Burn In'
        elif self.current_deployment_status() == 'deploy':
            deployment_status_label = 'Deployed'
        elif self.current_deployment_status() == 'recover':
            deployment_status_label = 'Recovered'
        elif self.current_deployment_status() == 'retire':
            deployment_status_label = 'Retired'

        return deployment_status_label

    def get_deployment_progress_bar(self):
        deployment_progress_bar = None
        # Set variables for Deployment Status bar in Bootstrap
        if self.current_deployment_status() == 'create':
            deployment_progress_bar = {
                'bar_class': 'bg-success',
                'bar_width': 20,
            }
        elif self.current_deployment_status() == 'burnin':
            deployment_progress_bar = {
                'bar_class': 'bg-danger',
                'bar_width': 40,
            }
        elif self.current_deployment_status() == 'deploy':
            deployment_progress_bar = {
                'bar_class': None,
                'bar_width': 60,
            }
        elif self.current_deployment_status() == 'recover':
            deployment_progress_bar = {
                'bar_class': 'bg-warning',
                'bar_width': 80,
            }
        elif self.current_deployment_status() == 'retire':
            deployment_progress_bar = {
                'bar_class': 'bg-info',
                'bar_width': 100,
            }

        return deployment_progress_bar


class Inventory(MPTTModel):
    INCOMING = 'incoming'
    OUTGOING = 'outgoing'
    TEST_TYPES = (
        (INCOMING, 'Incoming Test'),
        (OUTGOING, 'Outgoing Test'),
    )

    TEST_RESULTS = (
            (None, "-"),
            (True, "Pass"),
            (False, "Fail"),
    )

    FLAG_TYPES = (
            (True, "Flagged"),
            (False, "Unflagged"),
    )
    serial_number = models.CharField(max_length=255, unique=True, db_index=True)
    old_serial_number = models.CharField(max_length=255, unique=False, blank=True)
    part = models.ForeignKey(Part, related_name='inventory',
                             on_delete=models.CASCADE, null=True, blank=False, db_index=True)
    revision = models.ForeignKey(Revision, related_name='inventory',
                             on_delete=models.SET_NULL, null=True, blank=False, db_index=True)
    location = TreeForeignKey(Location, related_name='inventory',
                              on_delete=models.SET_NULL, null=True, blank=False, db_index=True)
    parent = TreeForeignKey('self', related_name='children',
                            on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    deployment = models.ForeignKey(Deployment, related_name='inventory',
                                   on_delete=models.SET_NULL, null=True, blank=True)
    build = models.ForeignKey(Build, related_name='inventory',
                              on_delete=models.SET_NULL, null=True, blank=True)
    assembly_part = TreeForeignKey(AssemblyPart, related_name='inventory',
                                   on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    assigned_destination_root = TreeForeignKey('self', related_name='assigned_children',
                                               on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    detail = models.TextField(blank=True)
    test_result = models.NullBooleanField(blank=False, choices=TEST_RESULTS)
    test_type = models.CharField(max_length=20, choices=TEST_TYPES, null=True, blank=True)
    flag = models.BooleanField(choices=FLAG_TYPES, blank=False, default=False)
    time_at_sea = models.DurationField(default=timedelta(minutes=0), null=True, blank=True)

    tracker = FieldTracker(fields=['location', 'deployment', 'parent', 'build'])

    class MPTTMeta:
        order_insertion_by = ['serial_number']

    def __str__(self):
        return self.serial_number

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return 'inventory'

    def get_absolute_url(self):
        return reverse('inventory:ajax_inventory_detail', kwargs={ 'pk': self.pk })

    def get_descendants_with_self(self):
        tree = self.get_descendants(include_self=True)
        return tree

    def get_latest_action(self):
        try:
            action = self.actions.latest()
            return action
        except:
            return None

    def get_latest_build(self):
        try:
            action = self.actions.filter(build__isnull=False).latest()
            return action.build
        except:
            return None

    def get_latest_parent(self):
        try:
            action = self.actions.filter(parent__isnull=False).latest()
            return action.parent
        except:
            return None

    def location_changed(self):
        current_location = self.location
        last_location = self.get_latest_action().location
        if current_location != last_location:
            return True
        return False

    # Return True item removed from Parent
    def parent_changed(self):
        current_parent = self.parent
        last_parent = self.get_latest_parent()
        if current_parent != last_parent:
            return True
        return False

    def get_latest_deployment(self):
        try:
            action = self.actions.filter(deployment__isnull=False).latest()
            return action.deployment
        except:
            return None

    # method to create new Action model records to track Inventory/User
    def create_action_record(self, user, action_type, detail='', created_at=None, cruise=None):
        # Add Try block here when done
        build = self.build
        deployment = None
        if build:
            deployment = self.build.get_latest_deployment()
        if not created_at:
            created_at = timezone.now()

        if action_type == 'invadd':
            detail = 'Item first added to Inventory. %s' % (detail)
        elif action_type == 'locationchange' or action_type == 'movetotrash':
            detail = 'Moved to %s from %s. %s' % (self.location, self.get_latest_action().location, detail)
        elif action_type == 'subchange':
            if not detail:
                if self.parent:
                    detail = 'Added to %s.' % (self.parent)
                else:
                    detail = 'Removed from %s.' % (self.get_latest_parent())
        elif action_type == 'addtobuild':
            detail = 'Moved to %s.' % (build)
        elif action_type == 'removefrombuild':
            build = self.get_latest_build()
            detail = 'Removed from %s. %s' % (build, detail)
        elif action_type == 'assigndest':
            detail = 'Destination assigned - %s.' % (self.assembly_part.assembly_revision)
        elif action_type == 'removedest':
            detail = 'Destination Assignment removed. %s' % (detail)
        elif action_type == 'test':
            detail = '%s: %s. %s' % (self.get_test_type_display(), self.get_test_result_display(), detail)
        elif action_type == 'startdeployment':
            detail = '%s %s started' % (labels['label_deployments_app_singular'], deployment)
        elif action_type == 'deploymenttosea':
            detail = 'Deployed to field on %s.' % (deployment)
            if cruise:
                detail = '%s Cruise: %s' % (detail, cruise)
        elif action_type == 'deploymentrecover':
            build = self.get_latest_build()
            deployment = self.get_latest_deployment()
            detail = 'Recovered from %s. %s' % (deployment, detail)
            if cruise:
                detail = '%s Cruise: %s' % (detail, cruise)

        action_record = Action.objects.create(action_type=action_type,
                                              object_type=self.get_object_type(),
                                              detail=detail,
                                              location=self.location,
                                              parent=self.parent,
                                              build=build,
                                              deployment=deployment,
                                              cruise=cruise,
                                              user=user,
                                              inventory=self,
                                              created_at=created_at)
        return action_record

    # get the most recent Deploy to Sea and Recover from Sea action timestamps, add this time delta to the time_at_sea column
    def update_time_at_sea(self):
        try:
            action_deploy_to_sea = self.actions.filter(action_type='deploymenttosea').latest()
        except Action.DoesNotExist:
            action_deploy_to_sea = None

        try:
            action_recover = self.actions.filter(action_type='deploymentrecover').latest()
        except Action.DoesNotExist:
            action_recover = None

        if action_deploy_to_sea and action_recover:
            latest_time_at_sea =  action_recover.created_at - action_deploy_to_sea.created_at
        else:
            latest_time_at_sea = timedelta(minutes=0)

        # add to existing Time at Sea duration
        self.time_at_sea = self.time_at_sea + latest_time_at_sea
        self.save()

    # get the Total Time at Sea by adding historical sea time and current deployment sea time
    def total_time_at_sea(self):
        try:
            total_time_at_sea = self.time_at_sea + self.current_deployment_time_at_sea()
            return total_time_at_sea
        except:
            return timedelta(minutes=0)

    # get the time at sea for the current Deployment only (if item is at sea)
    def current_deployment_time_at_sea(self):
        if self.build and self.build.current_deployment() and self.build.current_deployment().current_deployment_status() == 'deploy':
            try:
                action_deploy_to_sea = self.actions.filter(action_type='deploymenttosea').latest()
            except Action.DoesNotExist:
                action_deploy_to_sea = None

            if action_deploy_to_sea:
                now = timezone.now()
                current_time_at_sea = now - action_deploy_to_sea.created_at
                return current_time_at_sea
            return timedelta(minutes=0)
        return timedelta(minutes=0)

    # get the Deployment burnin action for deployment_event
    def get_deployment_burnin_event(self, deployment_event):
        try:
            action = self.actions.filter(action_type='deploymentburnin') \
                                               .filter(created_at__gte=deployment_event.created_at) \
                                               .filter(deployment=deployment_event.deployment).last()
            return action
        except Action.DoesNotExist:
            return None

    # get the Deployment deploymenttosea action for deployment_event
    def get_deployment_to_sea_event(self, deployment_event):
        try:
            action = self.actions.filter(action_type='deploymenttosea') \
                                               .filter(created_at__gte=deployment_event.created_at) \
                                               .filter(deployment=deployment_event.deployment).last()
            return action
        except Action.DoesNotExist:
            return None

    # get the Deployment recovery action for deployment_event
    def get_deployment_recovery_event(self, deployment_event):
        try:
            action = self.actions.filter(action_type='deploymentrecover') \
                                               .filter(created_at__gte=deployment_event.created_at) \
                                               .filter(deployment=deployment_event.deployment).last()
            return action
        except Action.DoesNotExist:
            return None

    # get the Deployment retire action for deployment_event
    def get_deployment_retire_event(self, deployment_event):
        try:
            action = self.actions.filter(action_type='deploymentretire') \
                                               .filter(created_at__gte=deployment_event.created_at) \
                                               .filter(deployment=deployment_event.deployment).last()
            return action
        except Action.DoesNotExist:
            return None

    # get the time at sea for any Deployment event
    def deployment_time_at_sea(self, deployment_event):
        action_deploy_to_sea = self.get_deployment_to_sea_event(deployment_event)
        action_recover = self.get_deployment_recovery_event(deployment_event)

        if action_deploy_to_sea:
            if action_recover:
                time_on_deployment = action_recover.created_at - action_deploy_to_sea.created_at
                return time_on_deployment
            # If no recovery, item is still at sea
            now = timezone.now()
            time_on_deployment = now - action_deploy_to_sea.created_at
            return time_on_deployment
        return timedelta(minutes=0)

    # get queryset of all Deployments for this Item
    def get_deployment_history(self):
        deployment_events = self.actions.filter(action_type='startdeployment')
        return deployment_events

    # get a Dict of data points for a Deployment event
    def get_deployment_data(self, deployment_event):
        if deployment_event:
            # get deployment cycle events
            deployment_burnin_event = self.get_deployment_burnin_event(deployment_event)
            deployment_to_sea_event = self.get_deployment_to_sea_event(deployment_event)
            deployment_recovery_event = self.get_deployment_recovery_event(deployment_event)
            deployment_retire_event = self.get_deployment_retire_event(deployment_event)
            # get time in field/sea
            time_at_sea = self.deployment_time_at_sea(deployment_event)
            # Populate percentage variable is the deployment_to_sea_event exists
            deployment_percentage = None
            if deployment_to_sea_event:
                # calculate percentage of total build deployment item was deployed
                try:
                    deployment_percentage = int(time_at_sea / deployment_event.deployment.get_deployment_time_at_sea() * 100)
                    if deployment_percentage > 100:
                        deployment_percentage = 100
                except:
                    pass

            # create dictionary of location details
            deployment_data = {
                'time_at_sea':  time_at_sea,
                'deployment_percentage': deployment_percentage,
                'deployment_burnin_event': deployment_burnin_event,
                'deployment_to_sea_event': deployment_to_sea_event,
                'deployment_recovery_event': deployment_recovery_event,
                'deployment_retire_event': deployment_retire_event,
            }
            return deployment_data
        return None

class DeploymentSnapshot(models.Model):
    deployment = models.ForeignKey(Deployment, related_name='deployment_snapshot',
                                   on_delete=models.CASCADE, null=True, blank=True)
    location = TreeForeignKey(Location, related_name='deployment_snapshot',
                              on_delete=models.SET_NULL, null=True, blank=False, db_index=True)
    snapshot_location = TreeForeignKey(Location, related_name='deployment_snapshot_location',
                              on_delete=models.SET_NULL, null=True, blank=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return '%s (%s)' % (self.deployment.deployment_number, self.deployment.final_location.location_id)

    def get_deployment_label(self):
        return '%s (%s)' % (self.deployment.deployment_number, self.deployment.final_location.location_id)


class InventorySnapshot(MPTTModel):
    inventory = models.ForeignKey(Inventory, related_name='inventory_snapshot',
                                 on_delete=models.SET_NULL, null=True, blank=True)
    parent = TreeForeignKey('self', related_name='children',
                            on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    deployment = models.ForeignKey(DeploymentSnapshot, related_name='inventory_snapshot',
                                   on_delete=models.CASCADE, null=True, blank=True)
    location = TreeForeignKey(Location, related_name='inventory_snapshot',
                              on_delete=models.SET_NULL, null=True, blank=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    order = models.CharField(max_length=255, null=False, blank=True, db_index=True)

    class MPTTMeta:
        order_insertion_by = ['order']

    def __str__(self):
        return self.inventory.serial_number


class Action(models.Model):
    INVADD = 'invadd'
    INVCHANGE = 'invchange'
    LOCATIONCHANGE = 'locationchange'
    SUBCHANGE = 'subchange'
    ADDTOBUILD = 'addtobuild'
    REMOVEFROMBUILD = 'removefrombuild'
    STARTDEPLOYMENT = 'startdeployment'
    DEPLOYMENTBURNIN = 'deploymentburnin'
    DEPLOYMENTTOSEA = 'deploymenttosea'
    DEPLOYMENTUPDATE = 'deploymentupdate'
    DEPLOYMENTRECOVER = 'deploymentrecover'
    DEPLOYMENTRETIRE = 'deploymentretire'
    ASSIGNDEST = 'assigndest'
    REMOVEDEST = 'removedest'
    TEST = 'test'
    NOTE = 'note'
    HISTORYNOTE = 'historynote'
    TICKET = 'ticket'
    FIELDCHANGE = 'fieldchange'
    FLAG = 'flag'
    MOVETOTRASH = 'movetotrash'
    ACTION_TYPES = (
        (INVADD, 'Add Inventory'),
        (INVCHANGE, 'Inventory Change'),
        (LOCATIONCHANGE, 'Location Change'),
        (SUBCHANGE, 'Sub-%s Change' % (labels['label_assemblies_app_singular'])),
        (ADDTOBUILD, 'Add to %s' % (labels['label_builds_app_singular'])),
        (REMOVEFROMBUILD, 'Remove from %s' % (labels['label_builds_app_singular'])),
        (STARTDEPLOYMENT, 'Start %s' % (labels['label_deployments_app_singular'])),
        (DEPLOYMENTBURNIN, '%s Burnin' % (labels['label_deployments_app_singular'])),
        (DEPLOYMENTTOSEA, '%s to Field' % (labels['label_deployments_app_singular'])),
        (DEPLOYMENTUPDATE, '%s Update' % (labels['label_deployments_app_singular'])),
        (DEPLOYMENTRECOVER, '%s Recovery' % (labels['label_deployments_app_singular'])),
        (DEPLOYMENTRETIRE, '%s Retired' % (labels['label_deployments_app_singular'])),
        (ASSIGNDEST, 'Assign Destination'),
        (REMOVEDEST, 'Remove Destination'),
        (TEST, 'Test'),
        (NOTE, 'Note'),
        (HISTORYNOTE, 'Historical Note'),
        (TICKET, 'Work Ticket'),
        (FIELDCHANGE, 'Field Change'),
        (FLAG, 'Flag'),
        (MOVETOTRASH, 'Move to Trash'),
    )
    inventory = models.ForeignKey(Inventory, related_name='actions',
                                  on_delete=models.CASCADE, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    object_type =  models.CharField(max_length=20, null=False, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    detail = models.TextField(blank=True)
    user = models.ForeignKey(User, related_name='actions',
                             on_delete=models.SET_NULL, null=True, blank=False)
    location = TreeForeignKey(Location, related_name='actions',
                              on_delete=models.SET_NULL, null=True, blank=False)
    deployment = models.ForeignKey(Deployment, related_name='actions',
                                   on_delete=models.SET_NULL, null=True, blank=True)
    build = models.ForeignKey(Build, related_name='actions',
                              on_delete=models.SET_NULL, null=True, blank=True)
    parent = models.ForeignKey(Inventory, related_name='parent_actions',
                              on_delete=models.SET_NULL, null=True, blank=True)
    cruise = models.ForeignKey(Cruise, related_name='actions',
                              on_delete=models.SET_NULL, null=True, blank=True)


    class Meta:
        ordering = ['-created_at', '-id']
        get_latest_by = 'created_at'

    def __str__(self):
        return self.get_action_type_display()


class PhotoNote(models.Model):
    photo = models.FileField(upload_to='notes/',
                             validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif', 'csv'])])
    inventory = models.ForeignKey(Inventory, related_name='photos',
                                 on_delete=models.CASCADE, null=True, blank=True)
    action = models.ForeignKey(Action, related_name='photos',
                                 on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, related_name='photos',
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


class DeploymentAction(models.Model):
    DEPLOY = 'deploy'
    RECOVER = 'recover'
    RETIRE = 'retire'
    CREATE = 'create'
    BURNIN = 'burnin'
    DETAILS = 'details'
    ACT_TYPES = (
        (DEPLOY, 'Deployed to Field'),
        (RECOVER, 'Recovered from Field'),
        (RETIRE, 'Retired'),
        (CREATE, 'Created'),
        (BURNIN, 'Burn In'),
        (DETAILS, '%s Details' % (labels['label_deployments_app_singular'])),
    )
    action_type = models.CharField(max_length=20, choices=ACT_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    detail = models.TextField(blank=True)
    user = models.ForeignKey(User, related_name='deployment_actions',
                             on_delete=models.SET_NULL, null=True, blank=False)
    location = TreeForeignKey(Location, related_name='deployment_actions',
                              on_delete=models.SET_NULL, null=True, blank=False)
    deployment = models.ForeignKey(Deployment, related_name='deployment_actions',
                                 on_delete=models.CASCADE, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True,
                                    validators=[
                                        MaxValueValidator(90),
                                        MinValueValidator(0)
                                    ])
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True,
                                    validators=[
                                        MaxValueValidator(180),
                                        MinValueValidator(0)
                                    ])
    depth = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at', 'action_type']
        get_latest_by = 'created_at'

    def __str__(self):
        return self.get_action_type_display()
