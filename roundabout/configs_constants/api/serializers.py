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

from rest_framework import serializers
from rest_flex_fields import FlexFieldsModelSerializer

from ..models import *
from roundabout.parts.api.serializers import PartSerializer
from roundabout.inventory.models import Inventory, Deployment
from roundabout.parts.models import Part

API_VERSION = 'api_v1'

class ConfigEventSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':configs-constants/config-events-detail',
        lookup_field = 'pk',
    )
    inventory = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':inventory-detail',
        lookup_field = 'pk',
        queryset = Inventory.objects
    )
    deployment = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':deployment-detail',
        lookup_field = 'pk',
        queryset = Deployment.objects
    )
    config_values = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':configs-constants/config-values-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )

    class Meta:
        model = ConfigEvent
        fields = [
            'id',
            'url',
            'created_at',
            'updated_at',
            'configuration_date',
            'user_draft',
            'user_approver',
            'inventory',
            'deployment',
            'approved',
            'detail',
            'config_type',
            'config_values',
        ]

        expandable_fields = {
            'config_values': ('roundabout.configs_constants.api.serializers.ConfigValueSerializer', {'many': True}),
            'inventory': 'roundabout.inventory.api.serializers.InventorySerializer',
            'deployment': 'roundabout.builds.api.serializers.DeploymentSerializer',
        }


class ConfigNameEventSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':configs-constants/config-name-events-detail',
        lookup_field = 'pk',
    )
    part = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':part-templates/parts-detail',
        lookup_field = 'pk',
        queryset = Part.objects
    )
    config_names = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':configs-constants/config-names-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )

    class Meta:
        model = ConfigNameEvent
        fields = [
            'id',
            'url',
            'created_at',
            'updated_at',
            'user_draft',
            'user_approver',
            'part',
            'approved',
            'detail',
            'config_names'
        ]

        expandable_fields = {
            'part': 'roundabout.parts.api.serializers.PartSerializer',
            'config_names': ('roundabout.configs_constants.api.serializers.ConfigNameSerializer', {'many': True})
        }


class ConfigNameSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':configs-constants/config-names-detail',
        lookup_field = 'pk',
    )
    config_name_event = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':configs-constants/config-name-events-detail',
        lookup_field = 'pk',
        queryset = ConfigNameEvent.objects
    )
    config_values = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':configs-constants/config-values-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )
    part = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':part-templates/parts-detail',
        lookup_field = 'pk',
        queryset = Part.objects
    )

    class Meta:
        model = ConfigName
        fields = [
            'id',
            'url',
            'name',
            'config_type',
            'created_at',
            'deprecated',
            'part',
            'include_with_calibrations',
            'config_name_event',
            'config_values',
        ]

        expandable_fields = {
            'config_name_event': 'roundabout.configs_constants.api.serializers.ConfigNameEvent',
            'part': 'roundabout.parts.api.serializers.PartSerializer',
            'config_values': ('roundabout.configs_constants.api.serializers.ConfigValueSerializer', {'many': True}),
        }


class ConfigValueSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':configs-constants/config-values-detail',
        lookup_field = 'pk',
    )
    config_name = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':configs-constants/config-names-detail',
        lookup_field = 'pk',
        queryset = ConfigName.objects
    )
    config_event = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':configs-constants/config-events-detail',
        lookup_field = 'pk',
        queryset = ConfigEvent.objects
    )

    class Meta:
        model = ConfigValue
        fields = [
            'id',
            'url',
            'config_value',
            'notes',
            'created_at',
            'config_name',
            'config_event',
        ]

        expandable_fields = {
            'config_name': 'roundabout.configs_constants.api.serializers.ConfigNameSerializer',
            'config_event': 'roundabout.configs_constants.api.serializers.ConfigEventSerializer',
        }


class CoefficientValueSetSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':calibrations/coefficent-value-sets-detail',
        lookup_field = 'pk',
    )
    calibration_event = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':calibrations/calibration-events-detail',
        lookup_field = 'pk',
        queryset = CalibrationEvent.objects
    )
    coefficient_name = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':calibrations/coefficent-names-detail',
        lookup_field = 'pk',
        queryset = CoefficientName.objects
    )
    coefficient_values = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':calibrations/coefficent-values-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )

    class Meta:
        model = CoefficientValueSet
        fields = [
            'id',
            'url',
            'value_set',
            'notes',
            'created_at',
            'coefficient_name',
            'calibration_event',
            'coefficient_values',
        ]

        expandable_fields = {
            'calibration_event': 'roundabout.calibrations.api.serializers.CalibrationEventSerializer',
            'coefficient_name': 'roundabout.calibrations.api.serializers.CoefficientNameSerializer',
            'coefficient_values': ('roundabout.calibrations.api.serializers.CoefficientValueSerializer', {'many': True})
        }


class CoefficientValueSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':calibrations/coefficent-values-detail',
        lookup_field = 'pk',
    )
    coeff_value_set = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':calibrations/coefficent-value-sets-detail',
        lookup_field = 'pk',
        queryset = CoefficientValueSet.objects
    )

    class Meta:
        model = CoefficientValue
        fields = [
            'id',
            'url',
            'value',
            'original_value',
            'notation_format',
            'sigfig',
            'row',
            'created_at',
            'coeff_value_set',
        ]

        expandable_fields = {
            'coeff_value_set': 'roundabout.calibrations.api.serializers.CoefficientValueSetSerializer',
        }
