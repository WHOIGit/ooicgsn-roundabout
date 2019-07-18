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
from roundabout.moorings.models import MooringPart
from roundabout.assemblies.models import Assembly, AssemblyPart
from roundabout.builds.models import Build
from roundabout.users.models import User

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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['build', '-created_at']

    def __str__(self):
        if self.deployed_location:
            return '%s - %s' % (self.deployment_number, self.deployed_location)
        else:
            return '%s - %s' % (self.deployment_number, self.location.name)

    def get_deployment_label(self):
        return self.deployment_number

    def current_deployment_status(self):
        deployment_action = self.deployment_actions.first()
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
        # get the latest 'Deploy' action record to find lat/long/depth data
        action_record = DeploymentAction.objects.filter(deployment=self).filter(action_type='details').first()

        if action_record:
            # create dictionary of location details
            deploytosea_details = {
                'latitude':  action_record.latitude,
                'longitude': action_record.longitude,
                'depth': action_record.depth,
                'deploy_date': action_record.created_at,
            }

        return deploytosea_details

    # get the most recent Deploy to Sea and Recover from Sea action timestamps, find time delta for Total Time at sea
    def get_deployment_time_at_sea(self):
        deployment_time_at_sea = None

        try:
            action_deploy_to_sea = DeploymentAction.objects.filter(deployment=self).filter(action_type='deploy').latest('created_at')
        except DeploymentAction.DoesNotExist:
            action_deploy_to_sea = None

        try:
            action_recover = DeploymentAction.objects.filter(deployment=self).filter(action_type='recover').latest('created_at')
        except DeploymentAction.DoesNotExist:
            action_recover = None

        if action_deploy_to_sea and action_recover:
            deployment_time_at_sea =  action_recover.created_at - action_deploy_to_sea.created_at

        return deployment_time_at_sea

    def get_deployment_status_label(self):
        deployment_status_label = None
        # get short label text for Deployment status
        if self.current_deployment_status() == 'create':
            deployment_status_label = 'Initial Deployment'
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
    mooring_part = TreeForeignKey(MooringPart, related_name='inventory',
                                  on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
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
    whoi_number = models.CharField(max_length=255, unique=False, null=False, blank=True)
    ooi_property_number = models.CharField(max_length=255, unique=False, null=False, blank=True)
    custom_field_values = JSONField(blank=True, null=True)

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

    # get the most recent Deploy to Sea and Recover from Sea action timestamps, add this time delta to the time_at_sea column
    def update_time_at_sea(self):
        try:
            action_deploy_to_sea = Action.objects.filter(inventory=self).filter(action_type='deploymenttosea').latest('created_at')
        except Action.DoesNotExist:
            action_deploy_to_sea = None

        try:
            action_recover = Action.objects.filter(inventory=self).filter(action_type='deploymentrecover').latest('created_at')
        except Action.DoesNotExist:
            action_recover = None

        if action_deploy_to_sea and action_recover:
            latest_time_at_sea =  action_recover.created_at - action_deploy_to_sea.created_at
        else:
            latest_time_at_sea = timedelta(minutes=0)

        # add to existing Time at Sea duration
        self.time_at_sea = self.time_at_sea + latest_time_at_sea
        self.save()

    # get the time at sea for the current deployment only (if item is at sea)
    def current_deployment_time_at_sea(self):
        root_location = self.location.get_root()
        if root_location.root_type == 'Sea':
            try:
                action_deploy_to_sea = Action.objects.filter(inventory=self).filter(action_type='deploymenttosea').latest('created_at')
            except Action.DoesNotExist:
                action_deploy_to_sea = None

            if action_deploy_to_sea:
                now = timezone.now()
                current_time_at_sea = now - action_deploy_to_sea.created_at
                return current_time_at_sea
            else:
                return timedelta(minutes=0)
        else:
            return timedelta(minutes=0)

    # get the Total Time at Sea by adding historical sea time and current deployment sea time
    def total_time_at_sea(self):
        return self.time_at_sea + self.current_deployment_time_at_sea()


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
    DEPLOYMENTBURNIN = 'deploymentburnin'
    DEPLOYMENTTOSEA = 'deploymenttosea'
    DEPLOYMENTUPDATE = 'deploymentupdate'
    DEPLOYMENTRECOVER = 'deploymentrecover'
    ASSIGNDEST = 'assigndest'
    REMOVEDEST = 'removedest'
    TEST = 'test'
    NOTE = 'note'
    HISTORYNOTE = 'historynote'
    TICKET = 'ticket'
    FIELDCHANGE = 'fieldchange'
    FLAG = 'flag'
    MOVETOTRASH = 'movetotrash'
    ACT_TYPES = (
        (INVADD, 'Add Inventory'),
        (INVCHANGE, 'Inventory Change'),
        (LOCATIONCHANGE, 'Location Change'),
        (SUBCHANGE, 'Subassembly Change'),
        (ADDTOBUILD, 'Add to Build'),
        (REMOVEFROMBUILD, 'Remove from Build'),
        (DEPLOYMENTBURNIN, 'Deployment Burnin'),
        (DEPLOYMENTTOSEA, 'Deployment to Sea'),
        (DEPLOYMENTUPDATE, 'Deployment Update'),
        (DEPLOYMENTRECOVER, 'Deployment Recovered'),
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
    action_type = models.CharField(max_length=20, choices=ACT_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    detail = models.TextField(blank=True)
    user = models.ForeignKey(User, related_name='action',
                             on_delete=models.SET_NULL, null=True, blank=False)
    location = TreeForeignKey(Location, related_name='action',
                              on_delete=models.SET_NULL, null=True, blank=False)
    inventory = models.ForeignKey(Inventory, related_name='action',
                                 on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at', 'action_type']

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
        (DEPLOY, 'Deployed to Sea'),
        (RECOVER, 'Recovered from Sea'),
        (RETIRE, 'Retired'),
        (CREATE, 'Created'),
        (BURNIN, 'Burn In'),
        (DETAILS, 'Deployment Details'),
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

    def __str__(self):
        return self.get_action_type_display()
