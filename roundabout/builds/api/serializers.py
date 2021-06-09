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

from rest_flex_fields import FlexFieldsModelSerializer
from rest_framework import serializers
from rest_framework.reverse import reverse

from roundabout.assemblies.models import Assembly, AssemblyRevision
from roundabout.core.templatetags.common_tags import time_at_sea_display
from roundabout.cruises.models import Cruise
from roundabout.inventory.models import Deployment
from roundabout.locations.models import Location
from ..models import Build

# Import environment variables from .env files
import environ

env = environ.Env()
base_url = env("RDB_SITE_URL")
API_VERSION = "api_v1"


class BuildSerializer(
    serializers.HyperlinkedModelSerializer, FlexFieldsModelSerializer
):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":builds-detail",
        lookup_field="pk",
    )
    inventory = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":inventory-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )
    deployments = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":deployments-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )
    location = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":locations-detail",
        lookup_field="pk",
        queryset=Location.objects,
    )
    assembly = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assemblies-detail",
        lookup_field="pk",
        queryset=Assembly.objects,
    )
    assembly_revision = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assembly-revisions-detail",
        lookup_field="pk",
        queryset=AssemblyRevision.objects,
    )
    time_in_field = serializers.SerializerMethodField("get_time_in_field")
    actions = serializers.SerializerMethodField("get_actions")

    class Meta:
        model = Build
        fields = [
            "id",
            "url",
            "build_number",
            "location",
            "assembly",
            "assembly_revision",
            "inventory",
            "deployments",
            "build_notes",
            "created_at",
            "updated_at",
            "is_deployed",
            "time_in_field",
            "flag",
            "actions",
        ]

        expandable_fields = {
            "location": "roundabout.locations.api.serializers.LocationSerializer",
            "assembly": "roundabout.assemblies.api.serializers.AssemblySerializer",
            "assembly_revision": "roundabout.assemblies.api.serializers.AssemblyRevisionSerializer",
            "inventory": (
                "roundabout.inventory.api.serializers.InventorySerializer",
                {"many": True},
            ),
            "deployments": (
                "roundabout.builds.api.serializers.DeploymentSerializer",
                {"many": True},
            ),
            "actions": (
                "roundabout.inventory.api.serializers.ActionSerializer",
                {"many": True},
            ),
        }

    def get_time_in_field(self, obj):
        return time_at_sea_display(obj.time_at_sea)

    def get_actions(self, obj):
        # Get all the Root AssemblyParts only
        actions = obj.get_actions()
        actions_list = [
            reverse(
                API_VERSION + ":actions-detail",
                kwargs={"pk": action.id},
                request=self.context["request"],
            )
            for action in actions
        ]
        return actions_list


class DeploymentSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":deployments-detail",
        lookup_field="pk",
    )
    build = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":builds-detail",
        lookup_field="pk",
        queryset=Build.objects,
    )
    cruise_deployed = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":cruises-detail",
        lookup_field="pk",
        queryset=Cruise.objects,
    )
    cruise_recovered = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":cruises-detail",
        lookup_field="pk",
        queryset=Cruise.objects,
    )
    location = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":locations-detail",
        lookup_field="pk",
        queryset=Location.objects,
    )
    deployed_location = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":locations-detail",
        lookup_field="pk",
        queryset=Location.objects,
    )
    inventory_deployments = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":inventory-deployments-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )
    time_in_field = serializers.SerializerMethodField("get_time_in_field")

    class Meta:
        model = Deployment
        fields = [
            "id",
            "url",
            "deployment_number",
            "build",
            "cruise_deployed",
            "cruise_recovered",
            "deployment_start_date",
            "deployment_burnin_date",
            "deployment_to_field_date",
            "deployment_recovery_date",
            "deployment_retire_date",
            "current_status",
            "location",
            "deployed_location",
            "latitude",
            "longitude",
            "depth",
            "time_in_field",
            "inventory_deployments",
        ]

        expandable_fields = {
            "build": BuildSerializer,
            "cruise_deployed": "roundabout.cruises.api.serializers.CruiseSerializer",
            "cruise_recovered": "roundabout.cruises.api.serializers.CruiseSerializer",
            "location": "roundabout.locations.api.serializers.LocationSerializer",
            "deployed_location": "roundabout.locations.api.serializers.LocationSerializer",
            "inventory_deployments": (
                "roundabout.inventory.api.serializers.InventoryDeploymentSerializer",
                {"many": True},
            ),
        }

    def get_time_in_field(self, obj):
        return time_at_sea_display(obj.deployment_time_in_field)


class DeploymentOmsCustomSerializer(FlexFieldsModelSerializer):
    deployment_url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":deployments-detail",
        lookup_field="pk",
    )
    build_number = serializers.SerializerMethodField("get_build_number")
    build_url = serializers.HyperlinkedRelatedField(
        source="build",
        view_name=API_VERSION + ":builds-detail",
        lookup_field="pk",
        queryset=Build.objects,
    )
    location_name = serializers.SerializerMethodField("get_location_name")
    location_url = serializers.HyperlinkedRelatedField(
        source="deployed_location",
        view_name=API_VERSION + ":locations-detail",
        lookup_field="pk",
        queryset=Location.objects,
    )
    assembly_parts = serializers.SerializerMethodField("get_assembly_parts")

    class Meta:
        model = Deployment
        fields = [
            "build_url",
            "build_number",
            "deployment_url",
            "deployment_number",
            "location_name",
            "location_url",
            "current_status",
            "latitude",
            "longitude",
            "assembly_parts",
        ]

    def get_build_id(self, obj):
        if obj.build:
            return obj.build.id
        return None

    def get_build_number(self, obj):
        if obj.build:
            return obj.build.build_number
        return None

    def get_location_id(self, obj):
        if obj.deployed_location:
            return obj.deployed_location.id
        return None

    def get_location_name(self, obj):
        if obj.deployed_location:
            return obj.deployed_location.name
        return None

    def get_assembly_parts(self, obj):
        # Use the InventoryDeployment related model to get historical list of Inventory items
        # on each Deployment
        inventory_dep_qs = obj.inventory_deployments.exclude(
            current_status=Deployment.DEPLOYMENTRETIRE
        ).select_related("inventory")
        assembly_parts = []

        for inv in inventory_dep_qs:
            # get all config_events for this Inventory/Deployment
            configuration_values = []
            config_events = inv.inventory.inventory_configevents.filter(
                deployment=inv.deployment
            ).prefetch_related("config_values")
            if config_events:
                for event in config_events:
                    for value in event.config_values.all():
                        configuration_values.append(
                            {
                                "name": value.config_name.name,
                                "value": value.config_value,
                            }
                        )

            # get all calibration_events for this Inventory/Deployment
            # need to get the CalibrationEvent that matches the Deployment date
            # calibration_date field sets the range for valid Calibration Events
            calibration_values = []
            if inv.inventory.inventory_calibrationevents.exists():
                for event in inv.inventory.inventory_calibrationevents.all():
                    # find the CalibrationEvent valid date range that matches Deployment date
                    first_date, last_date = event.get_valid_calibration_range()
                    if (
                        inv.deployment_to_field_date
                        and first_date < inv.deployment_to_field_date < last_date
                    ):
                        for value in event.coefficient_value_sets.all():
                            calibration_values.append(
                                {
                                    "name": value.coefficient_name.calibration_name,
                                    "value": value.value_set,
                                }
                            )
                        break

            # get all constant_default_events for this Inventory/Deployment
            constant_default_values = []
            if inv.inventory.inventory_constdefaultevents.exists():
                for event in inv.inventory.inventory_constdefaultevents.all():
                    for value in event.constant_defaults.all():
                        constant_default_values.append(
                            {
                                "name": value.config_name.name,
                                "value": value.default_value,
                            }
                        )

            # get all custom_fields for this Inventory/Deployment
            custom_fields = []
            if inv.inventory.fieldvalues.exists():
                inv_custom_fields = inv.inventory.fieldvalues.filter(
                    is_current=True
                ).select_related("field")
                # create initial empty dict
                for field in inv_custom_fields:
                    custom_fields.append(
                        {
                            "name": field.field.field_name,
                            "value": field.field_value,
                        }
                    )

            # set up URL link fields
            request = self.context.get("request")
            inventory_url = reverse(
                "api_v1:inventory-detail",
                kwargs={"pk": inv.inventory_id},
                request=request,
            )
            assembly_part_url = reverse(
                "api_v1:assembly-templates/assembly-parts-detail",
                kwargs={"pk": inv.assembly_part_id},
                request=request,
            )

            if inv.assembly_part and inv.assembly_part.parent:
                parent_assembly_part_url = reverse(
                    "api_v1:assembly-templates/assembly-parts-detail",
                    kwargs={"pk": inv.assembly_part.parent_id},
                    request=request,
                )
                parent_assembly_part_id = inv.assembly_part.parent.id
            else:
                parent_assembly_part_url = None
                parent_assembly_part_id = None
            # create object to populate the "assembly_part" list
            item_obj = {
                "assembly_part_url": assembly_part_url,
                "assembly_part_id": inv.assembly_part.id,
                "part_name": inv.inventory.part.name,
                "part_type": inv.inventory.part.part_type.name
                if inv.inventory.part.part_type
                else None,
                "parent_assembly_part_url": parent_assembly_part_url,
                "parent_assembly_part_id": parent_assembly_part_id,
                "inventory_url": inventory_url,
                "inventory_serial_number": inv.inventory.serial_number,
                "deployment_to_field_date": inv.deployment_to_field_date,
                "deployment_recovery_date": inv.deployment_recovery_date,
                "configuration_values": configuration_values,
                "calibration_values": calibration_values,
                "constant_default_values": constant_default_values,
                "custom_fields": custom_fields,
            }
            assembly_parts.append(item_obj)

        return assembly_parts


class DeploymentOmsCustom2Serializer(FlexFieldsModelSerializer):
    deployment_url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":deployments-detail",
        lookup_field="pk",
    )
    build_number = serializers.SerializerMethodField("get_build_number")
    build_url = serializers.HyperlinkedRelatedField(
        source="build",
        view_name=API_VERSION + ":builds-detail",
        lookup_field="pk",
        queryset=Build.objects,
    )
    location_name = serializers.SerializerMethodField("get_location_name")
    location_url = serializers.HyperlinkedRelatedField(
        source="deployed_location",
        view_name=API_VERSION + ":locations-detail",
        lookup_field="pk",
        queryset=Location.objects,
    )
    assembly_parts = serializers.SerializerMethodField("get_assembly_parts")

    class Meta:
        model = Deployment
        fields = [
            "build_url",
            "build_number",
            "deployment_url",
            "deployment_number",
            "location_name",
            "location_url",
            "current_status",
            "latitude",
            "longitude",
            "assembly_parts",
        ]

    def get_build_id(self, obj):
        if obj.build:
            return obj.build.id
        return None

    def get_build_number(self, obj):
        if obj.build:
            return obj.build.build_number
        return None

    def get_location_id(self, obj):
        if obj.deployed_location:
            return obj.deployed_location.id
        return None

    def get_location_name(self, obj):
        if obj.deployed_location:
            return obj.deployed_location.name
        return None

    def get_assembly_parts(self, obj):
        # Use the InventoryDeployment related model to get historical list of Inventory items
        # on each Deployment
        request = self.context.get("request")
        try:
            assembly_parts_qs = obj.build.assembly_revision.assembly_parts.all()
        except Exception as e:
            print(e)
            return None

        assembly_parts = []

        for ap in assembly_parts_qs:
            # get InventoryDeployment for this AssemblyPart
            inv = ap.inventory_deployments.filter(deployment=obj).first()

            if inv:
                # get all config_events for this Inventory/Deployment
                configuration_values = []
                config_events = inv.inventory.config_events.filter(
                    deployment=inv.deployment
                ).prefetch_related("config_values")
                if config_events:
                    for event in config_events:
                        for value in event.config_values.all():
                            configuration_values.append(
                                {
                                    "name": value.config_name.name,
                                    "value": value.config_value,
                                }
                            )

                # get all calibration_events for this Inventory/Deployment
                # need to get the CalibrationEvent that matches the Deployment date
                # calibration_date field sets the range for valid Calibration Events
                calibration_values = []
                if inv.inventory.calibration_events.exists():
                    for event in inv.inventory.calibration_events.all():
                        # find the CalibrationEvent valid date range that matches Deployment date
                        first_date, last_date = event.get_valid_calibration_range()
                        if (
                            inv.deployment_to_field_date
                            and first_date < inv.deployment_to_field_date < last_date
                        ):
                            for value in event.coefficient_value_sets.all():
                                calibration_values.append(
                                    {
                                        "name": value.coefficient_name.calibration_name,
                                        "value": value.value_set,
                                    }
                                )
                            break

                # get all constant_default_events for this Inventory/Deployment
                constant_default_values = []
                if inv.inventory.constant_default_events.exists():
                    for event in inv.inventory.constant_default_events.all():
                        for value in event.constant_defaults.all():
                            constant_default_values.append(
                                {
                                    "name": value.config_name.name,
                                    "value": value.default_value,
                                }
                            )

                # get all custom_fields for this Inventory/Deployment
                custom_fields = []
                if inv.inventory.fieldvalues.exists():
                    inv_custom_fields = inv.inventory.fieldvalues.filter(
                        is_current=True
                    ).select_related("field")
                    # create initial empty dict
                    for field in inv_custom_fields:
                        custom_fields.append(
                            {
                                "name": field.field.field_name,
                                "value": field.field_value,
                            }
                        )

                # set up URL link fields
                inventory_url = reverse(
                    "api_v1:inventory-detail",
                    kwargs={"pk": inv.inventory_id},
                    request=request,
                )
                # add Serial Number
                inventory_serial_number = inv.inventory.serial_number
            else:
                inventory_url = None
                inventory_serial_number = None
                configuration_values = None
                calibration_values = None
                constant_default_values = None
                custom_fields = None

            # get ConfigDefault for AssemblyPart
            config_default_values = []
            if ap.config_default_events.exists():
                for event in ap.config_default_events.all():
                    for value in event.config_defaults.all():
                        config_default_values.append(
                            {
                                "name": value.config_name.name,
                                "value": value.default_value,
                            }
                        )

            assembly_part_url = reverse(
                "api_v1:assembly-templates/assembly-parts-detail",
                kwargs={"pk": ap.id},
                request=request,
            )

            if ap.parent:
                parent_assembly_part_url = reverse(
                    "api_v1:assembly-templates/assembly-parts-detail",
                    kwargs={"pk": ap.parent_id},
                    request=request,
                )
                parent_assembly_part_id = ap.parent.id
            else:
                parent_assembly_part_url = None
                parent_assembly_part_id = None

            # create object to populate the "assembly_part" list
            ap_obj = {
                "assembly_part_url": assembly_part_url,
                "assembly_part_id": ap.id,
                "part_name": ap.part.name,
                "part_type": ap.part.part_type.name if ap.part.part_type else None,
                "parent_assembly_part_url": parent_assembly_part_url,
                "parent_assembly_part_id": parent_assembly_part_id,
                "config_default_values": config_default_values,
                "inventory_url": inventory_url,
                "inventory_serial_number": inventory_serial_number,
                "deployment_to_field_date": inv.deployment_to_field_date
                if inv
                else None,
                "deployment_recovery_date": inv.deployment_recovery_date
                if inv
                else None,
                "configuration_values": configuration_values,
                "calibration_values": calibration_values,
                "constant_default_values": constant_default_values,
                "custom_fields": custom_fields,
            }
            assembly_parts.append(ap_obj)

        return assembly_parts
