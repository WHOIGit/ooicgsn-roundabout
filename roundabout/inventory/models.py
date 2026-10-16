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

import datetime
import os
from datetime import timedelta

from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    FileExtensionValidator,
)
from django.urls import reverse
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey

from roundabout.assemblies.models import Assembly, AssemblyPart

# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels
from roundabout.cruises.models import Cruise, Vessel
from roundabout.locations.models import Location
from roundabout.parts.models import Part, Revision
from roundabout.users.models import User
from .managers import *

labels = set_app_labels()

# Private functions for use in Models
# ------------------------------------------------------------------------------


# Inventory/Deployment models
# ------------------------------------------------------------------------------
class Inventory(MPTTModel):
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    TEST_TYPES = (
        (INCOMING, "Incoming Test"),
        (OUTGOING, "Outgoing Test"),
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
    part = models.ForeignKey(
        Part,
        related_name="inventory",
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        db_index=True,
    )
    revision = models.ForeignKey(
        Revision,
        related_name="inventory",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        db_index=True,
    )
    location = TreeForeignKey(
        Location,
        related_name="inventory",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        db_index=True,
    )
    parent = TreeForeignKey(
        "self",
        related_name="children",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
    )
    build = models.ForeignKey(
        "builds.Build",
        related_name="inventory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    assembly_part = TreeForeignKey(
        AssemblyPart,
        related_name="inventory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
    )
    assigned_destination_root = TreeForeignKey(
        "self",
        related_name="assigned_children",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
    )
    bulk_upload_event = models.ForeignKey(
        "ooi_ci_tools.BulkUploadEvent",
        related_name="inventory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    detail = models.TextField(blank=True)
    test_result = models.BooleanField(null=True, blank=False, choices=TEST_RESULTS)
    test_type = models.CharField(
        max_length=20, choices=TEST_TYPES, null=True, blank=True
    )
    flag = models.BooleanField(choices=FLAG_TYPES, blank=False, default=False)
    # Deprecated as of v1.5
    _time_at_sea = models.DurationField(
        default=timedelta(minutes=0), null=True, blank=True
    )

    # tracker = FieldTracker(fields=['location', 'build'])

    class MPTTMeta:
        order_insertion_by = ["serial_number"]

    def __str__(self):
        return self.serial_number

    # get all Deployments "time in field", add them up for item's life total
    @property
    def time_at_sea(self):
        deployments = self.inventory_deployments.all()
        times = [dep.deployment_time_in_field for dep in deployments]
        total_time_in_field = sum(times, datetime.timedelta())
        return total_time_in_field

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return "inventory"

    def get_absolute_url(self):
        return reverse("inventory:ajax_inventory_detail", kwargs={"pk": self.pk})

    def get_descendants_with_self(self):
        tree = self.get_descendants(include_self=True)
        return tree

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
        if self.actions.exists():
            latest_action = self.actions.latest()
            if hasattr(latest_action, "location"):
                last_location = latest_action.location
                if current_location != last_location:
                    return True
        return False

    # Return True if item removed from Parent
    def parent_changed(self):
        current_parent = self.parent
        last_parent = self.get_latest_parent()
        if current_parent != last_parent:
            return True
        return False

    def current_deployment(self):
        try:
            current_deployment = self.inventory_deployments.get_active_deployment()
            return current_deployment
        except:
            return None

    def get_latest_deployment(self):
        try:
            latest_deployment = self.inventory_deployments.latest().deployment
            return latest_deployment
        except:
            return None


class InventoryHyperlink(models.Model):
    text = models.CharField(max_length=255, unique=False, blank=False, null=False)
    url = models.URLField(max_length=1000)
    parent = models.ForeignKey(
        Inventory,
        related_name="hyperlinks",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )


class DeploymentBase(models.Model):
    STARTDEPLOYMENT = "startdeployment"
    DEPLOYMENTBURNIN = "deploymentburnin"
    DEPLOYMENTTOFIELD = "deploymenttofield"
    DEPLOYMENTRECOVER = "deploymentrecover"
    DEPLOYMENTRETIRE = "deploymentretire"
    DEPLOYMENT_STATUS = (
        (STARTDEPLOYMENT, "Start %s" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTBURNIN, "%s Burnin" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTTOFIELD, "%s to Field" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTRECOVER, "%s Recovery" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTRETIRE, "%s Retired" % (labels["label_deployments_app_singular"])),
    )
    cruise_deployed = models.ForeignKey(
        Cruise,
        related_name="%(class)ss",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    cruise_recovered = models.ForeignKey(
        Cruise,
        related_name="recovered_%(class)ss",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    deployment_start_date = models.DateTimeField(default=timezone.now)
    deployment_burnin_date = models.DateTimeField(null=True, blank=True)
    deployment_to_field_date = models.DateTimeField(null=True, blank=True)
    deployment_recovery_date = models.DateTimeField(null=True, blank=True)
    deployment_retire_date = models.DateTimeField(null=True, blank=True)
    current_status = models.CharField(
        max_length=20, choices=DEPLOYMENT_STATUS, db_index=True, default=STARTDEPLOYMENT
    )

    class Meta:
        abstract = True
        ordering = ["-deployment_start_date"]
        get_latest_by = "deployment_start_date"

    def save(self, *args, **kwargs):
        # set the current_status by date actions
        if self.deployment_retire_date:
            self.current_status = DeploymentBase.DEPLOYMENTRETIRE
        elif self.deployment_recovery_date:
            self.current_status = DeploymentBase.DEPLOYMENTRECOVER
        elif self.deployment_to_field_date:
            self.current_status = DeploymentBase.DEPLOYMENTTOFIELD
        elif self.deployment_burnin_date:
            self.current_status = DeploymentBase.DEPLOYMENTBURNIN
        else:
            self.current_status = DeploymentBase.STARTDEPLOYMENT

        super().save(*args, **kwargs)

    # get the time at sea for any Deployment
    @property
    def deployment_time_in_field(self):
        if self.deployment_to_field_date:
            if self.deployment_recovery_date:
                time_on_deployment = (
                    self.deployment_recovery_date - self.deployment_to_field_date
                )
                return time_on_deployment
            # If no recovery, item is still at sea
            now = timezone.now()
            time_on_deployment = now - self.deployment_to_field_date
            return time_on_deployment
        return timedelta(minutes=0)

    # get the total time for any Inventory Deployment from Start to Retire
    @property
    def deployment_total_time(self):
        if self.deployment_start_date:
            if self.deployment_retire_date:
                time_on_deployment = (
                    self.deployment_retire_date - self.deployment_start_date
                )
                return time_on_deployment
            # If no retirement, deployment still active
            now = timezone.now()
            time_on_deployment = now - self.deployment_start_date
            return time_on_deployment
        return timedelta(minutes=0)

    def deployment_progress_bar(self):
        deployment_progress_bar = None
        # Set variables for Deployment/Inventory Deployment Status bar in Bootstrap
        if self.current_status == DeploymentBase.STARTDEPLOYMENT:
            deployment_progress_bar = {
                "bar_class": "bg-success",
                "bar_width": 20,
                "status_label": "Deployment Started",
            }
        elif self.current_status == DeploymentBase.DEPLOYMENTBURNIN:
            deployment_progress_bar = {
                "bar_class": "bg-danger",
                "bar_width": 40,
                "status_label": "Deployment Burn In",
            }
        elif self.current_status == DeploymentBase.DEPLOYMENTTOFIELD:
            deployment_progress_bar = {
                "bar_class": None,
                "bar_width": 60,
                "status_label": "Deployed to Field",
            }
        elif self.current_status == DeploymentBase.DEPLOYMENTRECOVER:
            deployment_progress_bar = {
                "bar_class": "bg-warning",
                "bar_width": 80,
                "status_label": "Deployment Recovered",
            }
        elif self.current_status == DeploymentBase.DEPLOYMENTRETIRE:
            deployment_progress_bar = {
                "bar_class": "bg-info",
                "bar_width": 100,
                "status_label": "Deployment Recovered",
            }
        return deployment_progress_bar


class Deployment(DeploymentBase):
    APPROVAL_STATUS = (
        (True, "Approved"),
        (False, "Draft"),
    )
    deployment_number = models.CharField(max_length=255, unique=False)
    location = TreeForeignKey(
        Location,
        related_name="deployments",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    final_location = TreeForeignKey(
        Location,
        related_name="final_deployments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    deployed_location = TreeForeignKey(
        Location,
        related_name="deployed_deployments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    build = models.ForeignKey(
        "builds.Build",
        related_name="deployments",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[MaxValueValidator(90), MinValueValidator(-90)],
        verbose_name="Drop Latitude",
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[MaxValueValidator(180), MinValueValidator(-180)],
        verbose_name="Drop Longitude",
    )
    depth = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Drop Depth"
    )
    surveyed_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[MaxValueValidator(90), MinValueValidator(-90)],
    )
    surveyed_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[MaxValueValidator(180), MinValueValidator(-180)],
    )
    surveyed_depth = models.PositiveIntegerField(null=True, blank=True)
    user_draft = models.ManyToManyField(
        User, related_name="reviewer_deployments", blank=True
    )
    user_approver = models.ManyToManyField(User, related_name="approver_deployments")
    approved = models.BooleanField(choices=APPROVAL_STATUS, blank=False, default=False)

    def __str__(self):
        if self.deployed_location:
            return "%s - %s" % (self.deployment_number, self.deployed_location)
        return "%s - %s" % (self.deployment_number, self.location.name)

    def get_actions(self):
        actions = self.actions.filter(object_type=Action.BUILD)
        return actions

    def get_sorted_reviewers(self):
        return self.user_draft.all().order_by("username")

    def get_sorted_approvers(self):
        return self.user_approver.all().order_by("username")


class InventoryDeployment(DeploymentBase):
    deployment = models.ForeignKey(
        Deployment,
        related_name="inventory_deployments",
        on_delete=models.CASCADE,
        null=False,
    )
    inventory = models.ForeignKey(
        Inventory,
        related_name="inventory_deployments",
        on_delete=models.CASCADE,
        null=False,
    )
    assembly_part = models.ForeignKey(
        "assemblies.AssemblyPart",
        related_name="inventory_deployments",
        on_delete=models.SET_NULL,
        null=True,
    )

    objects = InventoryDeploymentQuerySet.as_manager()

    def __str__(self):
        if self.deployment.deployed_location:
            return "%s - %s - %s" % (
                self.deployment.deployment_number,
                self.deployment.deployed_location,
                self.inventory,
            )
        return "%s - %s - %s" % (
            self.deployment.deployment_number,
            self.deployment.location,
            self.inventory,
        )

    @property
    def deployment_percentage_vs_build(self):
        # Populate percentage variable is the deployment_to_sea_event exists
        deployment_percentage = 0
        if self.deployment_to_field_date:
            # calculate percentage of total build deployment item was deployed
            if not self.deployment.deployment_time_in_field:
                deployment_percentage = 0
            elif not self.deployment_time_in_field:
                deployment_percentage = 0
            else:
                deployment_percentage = int(
                    self.deployment_time_in_field
                    / self.deployment.deployment_time_in_field
                    * 100
                )
            if deployment_percentage >= 99:
                deployment_percentage = 100
            return deployment_percentage

    def get_actions(self):
        actions = self.inventory.actions.filter(object_type=Action.INVENTORY).filter(
            inventory_deployment=self
        )
        return actions


class DeploymentSnapshot(models.Model):
    deployment = models.ForeignKey(
        Deployment,
        related_name="deployment_snapshot",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    location = TreeForeignKey(
        Location,
        related_name="deployment_snapshot",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        db_index=True,
    )
    snapshot_location = TreeForeignKey(
        Location,
        related_name="deployment_snapshot_location",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        db_index=True,
    )
    created_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return "%s (%s)" % (
            self.deployment.deployment_number,
            self.deployment.final_location.location_id,
        )

    def get_deployment_label(self):
        return "%s (%s)" % (
            self.deployment.deployment_number,
            self.deployment.final_location.location_id,
        )


class InventorySnapshot(MPTTModel):
    inventory = models.ForeignKey(
        Inventory,
        related_name="inventory_snapshot",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    parent = TreeForeignKey(
        "self",
        related_name="children",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
    )
    deployment = models.ForeignKey(
        DeploymentSnapshot,
        related_name="inventory_snapshot",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    location = TreeForeignKey(
        Location,
        related_name="inventory_snapshot",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        db_index=True,
    )
    created_at = models.DateTimeField(default=timezone.now)
    order = models.CharField(max_length=255, null=False, blank=True, db_index=True)

    class MPTTMeta:
        order_insertion_by = ["order"]

    def __str__(self):
        return self.inventory.serial_number


class Action(models.Model):
    # action_type choices
    ADD = "add"
    UPDATE = "update"
    LOCATIONCHANGE = "locationchange"
    SUBCHANGE = "subchange"
    ADDTOBUILD = "addtobuild"
    REMOVEFROMBUILD = "removefrombuild"
    STARTDEPLOYMENT = "startdeployment"
    REMOVEFROMDEPLOYMENT = "removefromdeployment"
    DEPLOYMENTBURNIN = "deploymentburnin"
    DEPLOYMENTTOFIELD = "deploymenttofield"
    DEPLOYMENTUPDATE = "deploymentupdate"
    DEPLOYMENTRECOVER = "deploymentrecover"
    DEPLOYMENTRETIRE = "deploymentretire"
    DEPLOYMENTDETAILS = "deploymentdetails"
    ASSIGNDEST = "assigndest"
    REMOVEDEST = "removedest"
    TEST = "test"
    NOTE = "note"
    HISTORYNOTE = "historynote"
    TICKET = "ticket"
    FIELDCHANGE = "fieldchange"
    FLAG = "flag"
    MOVETOTRASH = "movetotrash"
    RETIREBUILD = "retirebuild"
    REVIEWAPPROVE = "reviewapprove"
    REVIEWUNAPPROVE = "reviewunapprove"
    EVENTAPPROVE = "eventapprove"
    EVENTUNAPPROVE = "eventunapprove"
    CALCSVIMPORT = "calcsvimport"
    CALCSVUPDATE = "calcsvupdate"
    ACTION_TYPES = (
        (ADD, "Added to RDB"),
        (UPDATE, "Details updated"),
        (LOCATIONCHANGE, "Location Change"),
        (SUBCHANGE, "Sub-%s Change" % (labels["label_assemblies_app_singular"])),
        (ADDTOBUILD, "Add to %s" % (labels["label_builds_app_singular"])),
        (REMOVEFROMBUILD, "Remove from %s" % (labels["label_builds_app_singular"])),
        (STARTDEPLOYMENT, "Start %s" % (labels["label_deployments_app_singular"])),
        (REMOVEFROMDEPLOYMENT, "%s Ended" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTBURNIN, "%s Burnin" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTTOFIELD, "%s to Field" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTUPDATE, "%s Update" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTRECOVER, "%s Recovery" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTRETIRE, "%s Retired" % (labels["label_deployments_app_singular"])),
        (
            DEPLOYMENTDETAILS,
            "%s Details Updated" % (labels["label_deployments_app_singular"]),
        ),
        (ASSIGNDEST, "Assign Destination"),
        (REMOVEDEST, "Remove Destination"),
        (TEST, "Test"),
        (NOTE, "Note"),
        (HISTORYNOTE, "Historical Note"),
        (TICKET, "Work Ticket"),
        (FIELDCHANGE, "Field Change"),
        (FLAG, "Flag"),
        (MOVETOTRASH, "Move to Trash"),
        (RETIREBUILD, "Retire Build"),
        (REVIEWAPPROVE, "Reviewer approved Event"),
        (REVIEWUNAPPROVE, "Reviewer unapproved Event"),
        (EVENTAPPROVE, "Event Approved"),
        (EVENTUNAPPROVE, "Event Unapproved"),
        (CALCSVIMPORT, "CSV Uploaded"),
        (CALCSVUPDATE, "Updated by CSV"),
    )
    # object_type choices
    BUILD = "build"
    INVENTORY = "inventory"
    DEPLOYMENT = "deployment"
    CALEVENT = "calibrationevent"
    CONSTDEFEVENT = "constdefaultevent"
    CONFEVENT = "configevent"
    CONFDEFEVENT = "configdefaultevent"
    COEFFNAMEEVENT = "coefficientnameevent"
    CONFNAMEEVENT = "confignameevent"
    REFDESEVENT = "referencedesignatorevent"
    BULKUPLOAD = "bulkuploadevent"
    CRUISEEVENT = "cruiseevent"
    VESSELEVENT = "vesselevent"
    LOCATION = "location"
    VESSEL = "vessel"
    CRUISE = "cruise"
    OBJECT_TYPES = (
        (BUILD, "Build"),
        (INVENTORY, "Inventory"),
        (DEPLOYMENT, "Deployment"),
        (CALEVENT, "Calibration Event"),
        (CONSTDEFEVENT, "Constant Default Event"),
        (CONFEVENT, "Configuration/Constant Event"),
        (CONFDEFEVENT, "Configuration Default Event"),
        (COEFFNAMEEVENT, "Coefficient Name Event"),
        (CONFNAMEEVENT, "Configuration Name Event"),
        (LOCATION, "Location"),
        (VESSEL, "Vessel"),
        (CRUISE, "Cruise"),
        (REFDESEVENT, "Reference Designator Event"),
        (BULKUPLOAD, "Bulk Upload Event"),
        (CRUISEEVENT, "Cruise Event"),
        (VESSELEVENT, "Vessel Event"),
    )
    # deployment_type choices
    BUILD_DEPLOYMENT = "build_deployment"
    INVENTORY_DEPLOYMENT = "inventory_deployment"
    DEPLOYMENT_TYPES = (
        (BUILD_DEPLOYMENT, "Build Deployment"),
        (INVENTORY_DEPLOYMENT, "Inventory Deployment"),
    )

    inventory = models.ForeignKey(
        Inventory,
        related_name="actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    calibration_event = models.ForeignKey(
        "calibrations.CalibrationEvent",
        related_name="actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    const_default_event = models.ForeignKey(
        "configs_constants.ConstDefaultEvent",
        related_name="actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    config_event = models.ForeignKey(
        "configs_constants.ConfigEvent",
        related_name="actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    config_default_event = models.ForeignKey(
        "configs_constants.ConfigDefaultEvent",
        related_name="actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    coefficient_name_event = models.ForeignKey(
        "calibrations.CoefficientNameEvent",
        related_name="actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    config_name_event = models.ForeignKey(
        "configs_constants.ConfigNameEvent",
        related_name="actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    reference_designator_event = models.ForeignKey(
        "ooi_ci_tools.ReferenceDesignatorEvent",
        related_name="actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    bulk_upload_event = models.ForeignKey(
        "ooi_ci_tools.BulkUploadEvent",
        related_name="actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    cruise_event = models.ForeignKey(
        "ooi_ci_tools.CruiseEvent",
        related_name="actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    vessel_event = models.ForeignKey(
        "ooi_ci_tools.VesselEvent",
        related_name="actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, db_index=True)
    object_type = models.CharField(
        max_length=25, choices=OBJECT_TYPES, null=False, blank=True, db_index=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    detail = models.TextField(blank=True)
    user = models.ForeignKey(
        User, related_name="actions", on_delete=models.SET_NULL, null=True, blank=False
    )
    location = TreeForeignKey(
        Location,
        related_name="actions",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    location_parent = TreeForeignKey(
        Location,
        related_name="location_parent_actions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    deployment = models.ForeignKey(
        Deployment,
        related_name="actions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    inventory_deployment = models.ForeignKey(
        InventoryDeployment,
        related_name="actions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    build = models.ForeignKey(
        "builds.Build",
        related_name="actions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    parent = models.ForeignKey(
        Inventory,
        related_name="parent_actions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    cruise = models.ForeignKey(
        Cruise, related_name="actions", on_delete=models.SET_NULL, null=True, blank=True
    )
    vessel = models.ForeignKey(
        Vessel, related_name="actions", on_delete=models.SET_NULL, null=True, blank=True
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[MaxValueValidator(90), MinValueValidator(0)],
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[MaxValueValidator(180), MinValueValidator(0)],
    )
    depth = models.PositiveIntegerField(null=True, blank=True)
    deployment_type = models.CharField(
        max_length=20, choices=DEPLOYMENT_TYPES, null=False, blank=True, default=""
    )
    data = models.JSONField(null=True)

    objects = ActionQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]
        get_latest_by = "created_at"

    def __str__(self):
        return self.get_action_type_display()

    def get_parent(self):
        if self.object_type == self.BUILD:
            return self.build
        elif self.object_type == self.INVENTORY:
            return self.inventory
        elif self.object_type == self.DEPLOYMENT:
            if self.deployment_type == self.INVENTORY_DEPLOYMENT:
                return self.inventory_deployment
            else:
                # self.deployment_type == self.BUILD_DEPLOYMENT
                return self.deployment

        elif self.object_type == self.CALEVENT:
            return self.calibration_event
        elif self.object_type == self.CONFEVENT:
            return self.config_event

        elif self.object_type == self.CONSTDEFEVENT:
            return self.const_default_event
        elif self.object_type == self.CONFDEFEVENT:
            return self.config_default_event

        elif self.object_type == self.COEFFNAMEEVENT:
            return self.coefficient_name_event
        elif self.object_type == self.CONFNAMEEVENT:
            return self.config_name_event

        elif self.object_type == self.VESSEL:
            return self.vessel
        elif self.object_type == self.CRUISE:
            return self.cruise

        elif self.object_type == self.REFDESEVENT:
            return self.reference_designator_event

        elif self.object_type == self.BULKUPLOAD:
            return self.bulk_upload_event


class PhotoNote(models.Model):
    photo = models.FileField(
        upload_to="notes/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "pdf",
                    "doc",
                    "docx",
                    "xls",
                    "xlsx",
                    "png",
                    "jpg",
                    "jpeg",
                    "gif",
                    "csv",
                ]
            )
        ],
    )
    inventory = models.ForeignKey(
        Inventory,
        related_name="photos",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    action = models.ForeignKey(
        Action, related_name="photos", on_delete=models.CASCADE, null=True, blank=True
    )
    user = models.ForeignKey(
        User, related_name="photos", on_delete=models.SET_NULL, null=True, blank=False
    )

    def file_type(self):
        # get the file extension from file name
        name, extension = os.path.splitext(self.photo.name)
        # set the possible extensions for docs and images
        doc_types = [".pdf", ".doc", ".docx", ".xls", ".xlsx"]
        image_types = [".png", ".jpg", ".jpeg", ".gif"]

        if extension in doc_types:
            return "document"
        if extension in image_types:
            return "image"
        return "other"


class DeploymentAction(models.Model):
    STARTDEPLOYMENT = "startdeployment"
    DEPLOYMENTBURNIN = "deploymentburnin"
    DEPLOYMENTTOFIELD = "deploymenttofield"
    DEPLOYMENTUPDATE = "deploymentupdate"
    DEPLOYMENTRECOVER = "deploymentrecover"
    DEPLOYMENTRETIRE = "deploymentretire"
    DEPLOYMENTDETAILS = "deploymentdetails"
    ACT_TYPES = (
        (STARTDEPLOYMENT, "Start %s" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTBURNIN, "%s Burnin" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTTOFIELD, "%s to Field" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTUPDATE, "%s Update" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTRECOVER, "%s Recovery" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTRETIRE, "%s Retired" % (labels["label_deployments_app_singular"])),
        (DEPLOYMENTDETAILS, "%s Details" % (labels["label_deployments_app_singular"])),
    )
    action_type = models.CharField(max_length=20, choices=ACT_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    detail = models.TextField(blank=True)
    user = models.ForeignKey(
        User,
        related_name="deployment_actions",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    location = TreeForeignKey(
        Location,
        related_name="deployment_actions",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    deployment = models.ForeignKey(
        Deployment,
        related_name="deployment_actions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[MaxValueValidator(90), MinValueValidator(0)],
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[MaxValueValidator(180), MinValueValidator(0)],
    )
    depth = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "action_type"]
        get_latest_by = "created_at"

    def __str__(self):
        return self.get_action_type_display()


class InventoryTest(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class InventoryTestResult(models.Model):
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"
    UNKNOWN = "unknown"
    RESULT_TYPES = (
        (PASS, "Pass"),
        (FAIL, "Fail"),
        (PENDING, "Pending"),
        (UNKNOWN, "Reset to Unknown"),
    )
    result = models.CharField(max_length=20, choices=RESULT_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    inventory = models.ForeignKey(
        Inventory, related_name="test_results", on_delete=models.CASCADE
    )
    inventory_test = models.ForeignKey(
        InventoryTest, related_name="test_results", on_delete=models.CASCADE
    )
    is_current = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    user = models.ForeignKey(
        User,
        related_name="test_results",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = "created_at"

    def __str__(self):
        return f"{self.inventory.serial_number} - {self.inventory_test.name} - {self.result}"
