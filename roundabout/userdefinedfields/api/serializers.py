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

from roundabout.inventory.models import Inventory
from roundabout.parts.models import Part
from roundabout.users.models import User
from ..models import *

API_VERSION = 'api_v1'

class FieldSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':user-defined-fields/fields-detail',
        lookup_field = 'pk',
    )
    fieldvalues = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':user-defined-fields/field-values-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )
    parts = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':part-templates/parts-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )
    global_for_part_types = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':part-templates/part-types-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )

    class Meta:
        model = Field
        fields = [
            'id',
            'url',
            'field_name',
            'field_description',
            'field_type',
            'field_default_value',
            'choice_field_options',
            'global_for_part_types',
            'created_at',
            'updated_at',
            'parts',
            'fieldvalues',
        ]

        expandable_fields = {
            'parts': ('roundabout.parts.api.serializers.PartSerializer', {'many': True}),
            'global_for_part_types': ('roundabout.parts.api.serializers.PartTypeSerializer', {'many': True}),
            'fieldvalues': ('roundabout.userdefinedfields.api.serializers.FieldValueSerializer', {'many': True}),
        }


class FieldValueSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':user-defined-fields/field-values-detail',
        lookup_field = 'pk',
    )
    field = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':user-defined-fields/fields-detail',
        lookup_field = 'pk',
        queryset = Field.objects
    )
    part = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':part-templates/parts-detail',
        lookup_field = 'pk',
        queryset = Part.objects
    )
    inventory = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':inventory-detail',
        lookup_field = 'pk',
        queryset = Inventory.objects
    )
    user = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':users-detail',
        lookup_field = 'pk',
        queryset = User.objects
    )
    field_value = serializers.SerializerMethodField('get_field_value')

    class Meta:
        model = FieldValue
        fields = [
            'id',
            'url',
            'field_value',
            'field',
            'inventory',
            'part',
            'created_at',
            'updated_at',
            'user',
            'is_current',
            'is_default_value',
        ]

        expandable_fields = {
            'field': 'roundabout.userdefinedfields.api.serializers.FieldSerializer',
            'part': 'roundabout.parts.api.serializers.PartSerializer',
            'inventory': 'roundabout.inventory.api.serializers.InventorySerializer',
            'user': 'roundabout.users.api.serializers.UserSerializer',
        }

    def get_field_value(self, obj):
        return obj.get_field_value
