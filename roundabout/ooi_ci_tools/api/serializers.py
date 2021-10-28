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
from datetime import datetime
from rest_flex_fields import FlexFieldsModelSerializer
from rest_framework import serializers

from ..models import ReferenceDesignator, ReferenceDesignatorEvent
from roundabout.inventory.models import Deployment
from roundabout.assemblies.models import AssemblyPart
from roundabout.core.api.fields import ConstantField


API_VERSION = "api_v1"


class ReferenceDesignatorEventSerializer(FlexFieldsModelSerializer):
    id = serializers.ReadOnlyField()
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":reference-designator-events-detail",
        lookup_field="pk",
    )
    assembly_part = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assembly-parts-detail",
        lookup_field="pk",
        queryset=AssemblyPart.objects,
        allow_null=True,
    )
    reference_designators = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":reference-designators-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )

    class Meta:
        model = ReferenceDesignator
        fields = [
            "id",
            "url",
            "reference_designators",
            "assembly_part",
        ]

        expandable_fields = {
            "assembly_part": (
                "roundabout.assemblies.api.serializers.AssemblyPartSerializer",
            ),
            "reference_designators": (
                "roundabout.ooi_ci_tools.api.serializers.ReferenceDesignatorSerializer",
                {"many": True},
            ),
        }


class ReferenceDesignatorSerializer(FlexFieldsModelSerializer):
    id = serializers.ReadOnlyField()
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":reference-designators-detail",
        lookup_field="pk",
    )
    assembly_parts = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assembly-parts-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )
    refdes_event = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":reference-designator-events-detail",
        lookup_field="pk",
        queryset=ReferenceDesignatorEvent.objects,
        allow_null=True,
    )

    class Meta:
        model = ReferenceDesignator
        fields = [
            "id",
            "url",
            "refdes_name",
            "assembly_parts",
            "refdes_event",
            "toc_l1",
            "toc_l2",
            "toc_l3",
            "instrument",
            "manufacturer",
            "model",
            "min_depth",
            "max_depth",
        ]

        expandable_fields = {
            "assembly_part": (
                "roundabout.assemblies.api.serializers.AssemblyPartSerializer",
                {"many": True},
            )
        }


class CiRefDesDeploymentCustomSerializer(serializers.Serializer):
    deployment_url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":inventory-deployments-detail",
        lookup_field="pk",
    )
    referenceDesignator = serializers.SerializerMethodField()
    lastModifiedTimestamp = serializers.SerializerMethodField()
    xclass = ConstantField(value=".XDeployment")
    dataSource = ConstantField(value="Roundabout DB. Whoop Whoop!")
    eventType = ConstantField(value="Deployment")
    eventStartTime = serializers.SerializerMethodField()
    eventStopTime = serializers.SerializerMethodField()
    deployCruiseInfo = serializers.SerializerMethodField()
    recoverCruiseInfo = serializers.SerializerMethodField()
    sensor = serializers.SerializerMethodField()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # rename fields in representation to add disallowed python variable names
        representation["@class"] = representation["xclass"]
        representation.pop("xclass")
        return representation

    def get_referenceDesignator(self, obj):
        request_object = self.context["request"]
        reference_designator = request_object.query_params.get("reference_designator")
        return reference_designator

    def get_lastModifiedTimestamp(self, obj):
        return int(datetime.timestamp(datetime.utcnow()))

    def get_eventStartTime(self, obj):
        if obj.deployment_to_field_date:
            return int(datetime.timestamp(obj.deployment_to_field_date))
        return None

    def get_eventStopTime(self, obj):
        if obj.deployment_recovery_date:
            return int(datetime.timestamp(obj.deployment_recovery_date))
        return None

    def get_deployCruiseInfo(self, obj):
        # get CruiseInfo
        if obj.cruise_deployed:
            eventStopTime = None
            if obj.cruise_deployed.cruise_stop_date:
                eventStopTime = int(
                    datetime.timestamp(obj.cruise_deployed.cruise_stop_date)
                )

            deployCruiseInfo = {
                "eventName": obj.cruise_deployed.CUID,
                "eventType": "CRUISE_INFO",
                "eventStartTime": int(
                    datetime.timestamp(obj.cruise_deployed.cruise_start_date)
                ),
                "eventStopTime": eventStopTime,
                "uniqueCruiseIdentifier": obj.cruise_deployed.CUID,
                "shipName": obj.cruise_deployed.vessel.vessel_name,
            }
            return deployCruiseInfo
        return None

    def get_recoverCruiseInfo(self, obj):
        # get CruiseInfo
        if obj.cruise_recovered:
            eventStopTime = None
            if obj.cruise_recovered.cruise_stop_date:
                eventStopTime = int(
                    datetime.timestamp(obj.cruise_recovered.cruise_stop_date)
                )

            recoverCruiseInfo = {
                "eventName": obj.cruise_recovered.CUID,
                "eventType": "CRUISE_INFO",
                "eventStartTime": int(
                    datetime.timestamp(obj.cruise_recovered.cruise_start_date)
                ),
                "eventStopTime": eventStopTime,
                "uniqueCruiseIdentifier": obj.cruise_recovered.CUID,
                "shipName": obj.cruise_recovered.vessel.vessel_name,
            }
            return recoverCruiseInfo
        return None

    def get_sensor(self, obj):
        sensor = obj.inventory

        # get all calibration_events for this Inventory/Deployment
        # need to get the CalibrationEvent that matches the Deployment date
        # calibration_date field sets the range for valid Calibration Events
        calibrations = []
        if obj.inventory.inventory_calibrationevents.exists():
            for event in obj.inventory.inventory_calibrationevents.all():
                # find the CalibrationEvent valid date range that matches Deployment date
                first_date, last_date = event.get_valid_calibration_range()
                if (
                    obj.deployment_to_field_date
                    and first_date < obj.deployment_to_field_date < last_date
                ):

                    for value in event.coefficient_value_sets.all():
                        coeff_obj = {
                            "name": value.coefficient_name.calibration_name,
                            "calData": [],
                        }

                        coeff_obj["calData"].append(
                            {
                                "eventName": value.coefficient_name.calibration_name,
                                "eventStartTime": event.calibration_date,
                                "eventStopTime": None,
                                "value": value.value_set,
                            }
                        )
                        calibrations.append(coeff_obj)

        sensor_obj = {
            "name": sensor.serial_number,
            "uid": sensor.serial_number,
            "serialNumber": sensor.serial_number,
            "assetType": "Sensor",
            "description": sensor.part.name,
            "calibration": calibrations,
        }
        return sensor_obj

    def get_reference_designators(self, obj):
        # Use the InventoryDeployment related model to get historical list of Inventory items
        # on each Deployment
        inventory_dep_qs = obj.inventory_deployments.select_related("inventory")
        reference_designators = []

        for inv in inventory_dep_qs:
            if not inv.assembly_part:
                continue

            if not inv.assembly_part.reference_designator:
                print("NO REFDES")
                continue

            # get CruiseInfo
            if inv.cruise_deployed:
                eventStopTime = None
                if inv.cruise_deployed.cruise_stop_date:
                    eventStopTime = int(
                        datetime.timestamp(inv.cruise_deployed.cruise_stop_date)
                    )

                deployCruiseInfo = {
                    "eventName": inv.cruise_deployed.CUID,
                    "eventType": "CRUISE_INFO",
                    "eventStartTime": int(
                        datetime.timestamp(inv.cruise_deployed.cruise_start_date)
                    ),
                    "eventStopTime": eventStopTime,
                }
            else:
                deployCruiseInfo = {}
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

            # create object to populate the "assembly_part" list
            item_obj = {
                "@class": ".XDeployment",
                "lastModifiedTimestamp": int(
                    datetime.timestamp(inv.deployment_to_field_date)
                ),
                "eventName": inv.assembly_part.reference_designator.refdes_name,
                "eventType": "DEPLOYMENT",
                "eventStartTime": int(datetime.timestamp(inv.deployment_to_field_date)),
                "eventStopTime": int(datetime.timestamp(inv.deployment_recovery_date))
                if inv.deployment_recovery_date
                else None,
                "deployCruiseInfo": deployCruiseInfo,
                "referenceDesignator": inv.assembly_part.reference_designator.refdes_name,
            }
            reference_designators.append(item_obj)

        return reference_designators
