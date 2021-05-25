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

from roundabout.assemblies.models import AssemblyPart
from roundabout.builds.models import Build
from roundabout.calibrations.models import CalibrationEvent, CoefficientNameEvent
from roundabout.configs_constants.models import (
    ConstDefaultEvent,
    ConfigEvent,
    ConfigDefaultEvent,
    ConfigNameEvent,
)
from roundabout.core.templatetags.common_tags import time_at_sea_display
from roundabout.cruises.models import Cruise
from roundabout.locations.models import Location
from roundabout.parts.models import Part, Revision
from roundabout.users.models import User
from ..models import Inventory, InventoryDeployment, Deployment, Action, PhotoNote

API_VERSION = "api_v1"


class PhotoNoteSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":photos-detail",
        lookup_field="pk",
    )
    inventory = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":inventory-detail",
        lookup_field="pk",
        queryset=Inventory.objects,
    )
    action = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":actions-detail",
        lookup_field="pk",
        queryset=Action.objects,
    )
    user = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":users-detail",
        lookup_field="pk",
        queryset=User.objects,
    )

    class Meta:
        model = PhotoNote
        fields = ["id", "url", "photo", "inventory", "action", "user"]

        expandable_fields = {
            "inventory": "roundabout.inventory.api.serializers.InventorySerializer",
            "action": "roundabout.inventory.api.serializers.ActionSerializer",
            "user": "roundabout.users.api.serializers.UserSerializer",
        }


class ActionSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":actions-detail",
        lookup_field="pk",
    )
    inventory = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":inventory-detail",
        lookup_field="pk",
        queryset=Inventory.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    location = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":locations-detail",
        lookup_field="pk",
        queryset=Location.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    deployment = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":deployments-detail",
        lookup_field="pk",
        queryset=Deployment.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    inventory_deployment = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":inventory-deployments-detail",
        lookup_field="pk",
        queryset=InventoryDeployment.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    user = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":users-detail",
        lookup_field="pk",
        queryset=User.objects,
    )
    build = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":builds-detail",
        lookup_field="pk",
        queryset=Build.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    parent = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":inventory-detail",
        lookup_field="pk",
        queryset=Inventory.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    cruise = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":cruises-detail",
        lookup_field="pk",
        queryset=Cruise.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    calibration_event = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":calibrations/calibration-events-detail",
        lookup_field="pk",
        queryset=CalibrationEvent.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    coefficient_name_event = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":calibrations/coefficent-name-events-detail",
        lookup_field="pk",
        queryset=CoefficientNameEvent.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    const_default_event = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":configs-constants/const-default-events-detail",
        lookup_field="pk",
        queryset=ConstDefaultEvent.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    config_event = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":configs-constants/config-events-detail",
        lookup_field="pk",
        queryset=ConfigEvent.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    config_default_event = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":configs-constants/config-default-events-detail",
        lookup_field="pk",
        queryset=ConfigDefaultEvent.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    config_name_event = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":configs-constants/config-name-events-detail",
        lookup_field="pk",
        queryset=ConfigNameEvent.objects,
        required=False,
        allow_null=True,
        default=None,
    )
    photos = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":photos-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )

    class Meta:
        model = Action
        fields = [
            "id",
            "url",
            "action_type",
            "object_type",
            "created_at",
            "inventory",
            "location",
            "deployment",
            "inventory_deployment",
            "deployment_type",
            "detail",
            "user",
            "build",
            "parent",
            "cruise",
            "latitude",
            "longitude",
            "depth",
            "calibration_event",
            "const_default_event",
            "config_event",
            "config_default_event",
            "coefficient_name_event",
            "config_name_event",
            "photos",
        ]

        expandable_fields = {
            "inventory": "roundabout.inventory.api.serializers.InventorySerializer",
            "deployment": "roundabout.builds.api.serializers.DeploymentSerializer",
            "inventory_deployment": "roundabout.inventory.api.serializers.InventoryDeploymentSerializer",
            "location": "roundabout.locations.api.serializers.LocationSerializer",
            "user": "roundabout.users.api.serializers.UserSerializer",
            "build": "roundabout.builds.api.serializers.BuildSerializer",
            "parent": "roundabout.inventory.api.serializers.InventorySerializer",
            "cruise": "roundabout.cruises.api.serializers.CruiseSerializer",
            "calibration_event": "roundabout.calibrations.api.serializers.CalibrationEventSerializer",
            "coefficient_name_event": "roundabout.calibrations.api.serializers.CoefficientNameEventSerializer",
            "const_default_event": "roundabout.configs_constants.api.serializers.ConstDefaultEventSerializer",
            "config_event": "roundabout.configs_constants.api.serializers.ConfigEventSerializer",
            "config_default_event": "roundabout.configs_constants.api.serializers.ConfigDefaultEventSerializer",
            "config_name_event": "roundabout.configs_constants.api.serializers.ConfigNameEventSerializer",
            "photos": (
                "roundabout.users.api.serializers.PhotoNoteSerializer",
                {"many": True},
            ),
        }


class InventorySerializer(FlexFieldsModelSerializer):
    # custom_fields = serializers.SerializerMethodField('get_custom_fields')
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":inventory-detail",
        lookup_field="pk",
    )
    location = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":locations-detail",
        lookup_field="pk",
        queryset=Location.objects,
    )
    part = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":part-templates/parts-detail",
        lookup_field="pk",
        queryset=Part.objects,
    )
    revision = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":part-templates/revisions-detail",
        lookup_field="pk",
        queryset=Revision.objects,
    )
    parent = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":inventory-detail",
        lookup_field="pk",
        queryset=Inventory.objects,
    )
    children = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":inventory-detail",
        lookup_field="pk",
        many=True,
        read_only=True,
    )
    build = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":builds-detail",
        lookup_field="pk",
        queryset=Build.objects,
    )
    assembly_part = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assembly-parts-detail",
        lookup_field="pk",
        queryset=AssemblyPart.objects,
    )
    assigned_destination_root = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":inventory-detail",
        lookup_field="pk",
        queryset=Inventory.objects,
    )
    actions = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":actions-detail",
        lookup_field="pk",
        many=True,
        read_only=True,
    )
    fieldvalues = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":user-defined-fields/field-values-detail",
        lookup_field="pk",
        many=True,
        read_only=True,
    )
    inventory_deployments = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":inventory-deployments-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )
    inventory_calibrationevents = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":calibrations/calibration-events-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )
    inventory_configevents = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":configs-constants/config-events-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )
    inventory_constdefaultevents = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":configs-constants/const-default-events-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )
    time_in_field = serializers.SerializerMethodField("get_time_in_field")

    class Meta:
        model = Inventory
        fields = [
            "id",
            "url",
            "serial_number",
            "old_serial_number",
            "part",
            "location",
            "revision",
            "parent",
            "children",
            "build",
            "assembly_part",
            "assigned_destination_root",
            "created_at",
            "updated_at",
            "test_result",
            "test_type",
            "flag",
            "time_in_field",
            "inventory_calibrationevents",
            "inventory_configevents",
            "inventory_constdefaultevents",
            "actions",
            "fieldvalues",
            "inventory_deployments",
        ]

        expandable_fields = {
            "location": "roundabout.locations.api.serializers.LocationSerializer",
            "part": "roundabout.parts.api.serializers.PartSerializer",
            "revision": "roundabout.parts.api.serializers.RevisionSerializer",
            "parent": "roundabout.inventory.api.serializers.InventorySerializer",
            "build": "roundabout.builds.api.serializers.BuildSerializer",
            "assembly_part": "roundabout.assemblies.api.serializers.AssemblyPartSerializer",
            "assigned_destination_root": "roundabout.inventory.api.serializers.InventorySerializer",
            "children": (
                "roundabout.inventory.api.serializers.InventorySerializer",
                {"many": True},
            ),
            "inventory_calibrationevents": (
                "roundabout.calibrations.api.serializers.CalibrationEventSerializer",
                {"many": True},
            ),
            "inventory_configevents": (
                "roundabout.configs_constants.api.serializers.ConfigEventSerializer",
                {"many": True},
            ),
            "inventory_constdefaultevents": (
                "roundabout.configs_constants.api.serializers.ConstDefaultEventSerializer",
                {"many": True},
            ),
            "actions": (
                "roundabout.inventory.api.serializers.ActionSerializer",
                {"many": True},
            ),
            "fieldvalues": (
                "roundabout.userdefinedfields.api.serializers.FieldValueSerializer",
                {"many": True, "omit": ["field.fieldvalues"]},
            ),
            "inventory_deployments": (
                "roundabout.inventory.api.serializers.InventoryDeploymentSerializer",
                {"many": True},
            ),
        }

    def get_time_in_field(self, obj):
        return time_at_sea_display(obj.time_at_sea)

    """
    def get_custom_fields(self, obj):
        # Get this item's custom fields with most recent Values
        custom_fields = None

        if obj.fieldvalues.exists():
            obj_custom_fields = obj.fieldvalues.filter(is_current=True).select_related('field')
            # create initial empty dict
            custom_fields = {}

            for field in obj_custom_fields:
                custom_fields[field.field.field_name] = field.field_value
            return custom_fields
        else:
            return custom_fields
    """


class InventoryDeploymentSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":inventory-deployments-detail",
        lookup_field="pk",
    )
    inventory = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":inventory-detail",
        lookup_field="pk",
        queryset=Inventory.objects,
    )
    deployment = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":deployments-detail",
        lookup_field="pk",
        queryset=Deployment.objects,
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
    time_in_field = serializers.SerializerMethodField("get_time_in_field")

    class Meta:
        model = InventoryDeployment
        fields = [
            "id",
            "url",
            "deployment",
            "inventory",
            "cruise_deployed",
            "cruise_recovered",
            "deployment_start_date",
            "deployment_burnin_date",
            "deployment_to_field_date",
            "deployment_recovery_date",
            "deployment_retire_date",
            "current_status",
            "time_in_field",
        ]

        expandable_fields = {
            "inventory": "roundabout.inventory.api.serializers.InventorySerializer",
            "deployment": "roundabout.builds.api.serializers.DeploymentSerializer",
            "cruise_deployed": "roundabout.cruises.api.serializers.CruiseSerializer",
            "cruise_recovered": "roundabout.cruises.api.serializers.CruiseSerializer",
        }

    def get_time_in_field(self, obj):
        return time_at_sea_display(obj.deployment_time_in_field)


"""
# Need a "sub-serializer" to handle self refernce MPTT tree structures
class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data
"""
