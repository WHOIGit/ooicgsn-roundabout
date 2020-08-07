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
from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields import DynamicRelationField
from ..models import Inventory, Action, PhotoNote
from roundabout.locations.api.serializers import LocationSerializer
from roundabout.parts.api.serializers import PartSerializer


class PhotoNoteSerializer(DynamicModelSerializer):
    class Meta:
        model = PhotoNote
        fields = ['id', 'photo', 'inventory', 'action', 'user']


class ActionSerializer(DynamicModelSerializer):
    photos = DynamicRelationField('PhotoNoteSerializer', many=True)
    location = DynamicRelationField('LocationSerializer')

    class Meta:
        model = Action
        fields = [
            'id', 'action_type', 'object_type', 'created_at', 'inventory', \
            'location', 'deployment',  'inventory_deployment', 'deployment_type', \
            'detail', 'user', 'build', 'parent', 'cruise', 'latitude', 'longitude', \
            'depth', 'calibration_event', 'const_default_event', 'config_event', \
            'config_default_event',
        ]
        optional_fields = ['photos']


class InventorySerializer(DynamicModelSerializer):
    location = DynamicRelationField('LocationSerializer')
    part = DynamicRelationField('PartSerializer', read_only=True)
    custom_fields = serializers.SerializerMethodField('get_custom_fields')

    class Meta:
        model = Inventory
        fields = [
            'id', 'serial_number', 'old_serial_number', 'part', 'location', 'revision', \
            'parent', 'build', 'assembly_part', 'assigned_destination_root', 'created_at', \
            'updated_at', 'detail', 'test_result', 'test_type', 'flag', 'time_at_sea', 'custom_fields'
        ]

    def get_custom_fields(self, obj):
        # Get this item's custom fields with most recent Values
        if obj.fieldvalues.exists():
            obj_custom_fields = obj.fieldvalues.filter(is_current=True).select_related('field')
        else:
            obj_custom_fields = None
        # create initial empty dict
        custom_fields = {}

        if obj_custom_fields:
            for field in obj_custom_fields:
                custom_fields[field.field.field_name] = field.field_value

        return custom_fields
