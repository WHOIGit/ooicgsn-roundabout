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

from ..models import *

API_VERSION = 'api_v1'


class ConfigEventSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ':configs-constants/config-events-detail',
        lookup_field='pk',
    )
    inventory = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':inventory-detail',
        lookup_field='pk',
        queryset=Inventory.objects
    )
    deployment = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':deployments-detail',
        lookup_field='pk',
        queryset=Deployment.objects
    )
    config_values = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/config-values-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
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
        view_name=API_VERSION + ':configs-constants/config-name-events-detail',
        lookup_field='pk',
    )
    part = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':part-templates/parts-detail',
        lookup_field='pk',
        queryset=Part.objects
    )
    config_names = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/config-names-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )
    user_draft = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':users-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )
    user_approver = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':users-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )
    actions = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':actions-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
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
            'config_names',
            'actions',
        ]

        expandable_fields = {
            'part': 'roundabout.parts.api.serializers.PartSerializer',
            'config_names': ('roundabout.configs_constants.api.serializers.ConfigNameSerializer', {'many': True}),
            'user_draft': ('roundabout.users.api.serializers.UserSerializer', {'many': True}),
            'user_approver': ('roundabout.users.api.serializers.UserSerializer', {'many': True}),
            'actions': ('roundabout.inventory.api.serializers.ActionSerializer', {'many': True}),
        }


class ConfigNameSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ':configs-constants/config-names-detail',
        lookup_field='pk',
    )
    config_name_event = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/config-name-events-detail',
        lookup_field='pk',
        queryset=ConfigNameEvent.objects
    )
    config_values = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/config-values-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )
    constant_defaults = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/const-defaults-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )
    config_defaults = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/config-defaults-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )
    part = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':part-templates/parts-detail',
        lookup_field='pk',
        queryset=Part.objects
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
            'constant_defaults',
            'config_defaults',
        ]

        expandable_fields = {
            'config_name_event': 'roundabout.configs_constants.api.serializers.ConfigNameEvent',
            'part': 'roundabout.parts.api.serializers.PartSerializer',
            'config_values': ('roundabout.configs_constants.api.serializers.ConfigValueSerializer', {'many': True}),
            'constant_defaults': ('roundabout.configs_constants.api.serializers.ConstDefaultSerializer', {'many': True}),
            'config_defaults': ('roundabout.configs_constants.api.serializers.ConfigDefaultSerializer', {'many': True}),
        }


class ConfigValueSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ':configs-constants/config-values-detail',
        lookup_field='pk',
    )
    config_name = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/config-names-detail',
        lookup_field='pk',
        queryset=ConfigName.objects
    )
    config_event = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/config-events-detail',
        lookup_field='pk',
        queryset=ConfigEvent.objects
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


class ConstDefaultEventSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ':configs-constants/const-default-events-detail',
        lookup_field='pk',
    )
    inventory = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':inventory-detail',
        lookup_field='pk',
        queryset=Inventory.objects
    )
    constant_defaults = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/const-defaults-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )
    user_draft = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':users-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )
    user_approver = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':users-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )

    class Meta:
        model = ConstDefaultEvent
        fields = [
            'id',
            'url',
            'created_at',
            'updated_at',
            'user_draft',
            'user_approver',
            'inventory',
            'approved',
            'detail',
            'constant_defaults',
        ]

        expandable_fields = {
            'constant_defaults': ('roundabout.configs_constants.api.serializers.ConstDefaultSerializer', {'many': True}),
            'inventory': 'roundabout.inventory.api.serializers.InventorySerializer',
            'user_draft': ('roundabout.users.api.serializers.UserSerializer', {'many': True}),
            'user_approver': ('roundabout.users.api.serializers.UserSerializer', {'many': True}),
        }


class ConstDefaultSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ':configs-constants/const-defaults-detail',
        lookup_field='pk',
    )
    config_name = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/config-names-detail',
        lookup_field='pk',
        queryset=ConfigName.objects
    )
    const_event = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/const-default-events-detail',
        lookup_field='pk',
        queryset=ConstDefaultEvent.objects
    )

    class Meta:
        model = ConstDefault
        fields = [
            'id',
            'url',
            'default_value',
            'created_at',
            'const_event',
            'config_name',
        ]

        expandable_fields = {
            'config_name': 'roundabout.configs_constants.api.serializers.ConfigNameSerializer',
            'const_event': 'roundabout.configs_constants.api.serializers.ConstDefaultEventSerializer',
        }


class ConfigDefaultEventSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ':configs-constants/config-default-events-detail',
        lookup_field='pk',
    )
    assembly_part = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':assembly-templates/assembly-parts-detail',
        lookup_field='pk',
        queryset=AssemblyPart.objects
    )
    config_defaults = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/config-defaults-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )
    user_draft = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':users-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )
    user_approver = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':users-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )
    actions = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':actions-detail',
        many=True,
        read_only=True,
        lookup_field='pk',
    )

    class Meta:
        model = ConfigDefaultEvent
        fields = [
            'id',
            'url',
            'created_at',
            'updated_at',
            'user_draft',
            'user_approver',
            'assembly_part',
            'approved',
            'detail',
            'config_defaults',
            'actions',
        ]

        expandable_fields = {
            'config_defaults': ('roundabout.configs_constants.api.serializers.ConfigDefaultSerializer', {'many': True}),
            'assembly_part': 'roundabout.assemblies.api.serializers.AssemblyPartSerializer',
            'user_draft': ('roundabout.users.api.serializers.UserSerializer', {'many': True}),
            'user_approver': ('roundabout.users.api.serializers.UserSerializer', {'many': True}),
            'actions': ('roundabout.inventory.api.serializers.ActionSerializer', {'many': True}),
        }


class ConfigDefaultSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ':configs-constants/config-defaults-detail',
        lookup_field='pk',
    )
    config_name = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/config-names-detail',
        lookup_field='pk',
        queryset=ConfigName.objects
    )
    conf_def_event = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ':configs-constants/config-default-events-detail',
        lookup_field='pk',
        queryset=ConfigEvent.objects
    )

    class Meta:
        model = ConfigDefault
        fields = [
            'id',
            'url',
            'default_value',
            'created_at',
            'config_name',
            'conf_def_event',
        ]

        expandable_fields = {
            'config_name': 'roundabout.configs_constants.api.serializers.ConfigNameSerializer',
            'conf_def_event': 'roundabout.configs_constants.api.serializers.ConfigDefaultEventSerializer',
        }
