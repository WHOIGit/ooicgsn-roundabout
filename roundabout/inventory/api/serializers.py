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
from roundabout.calibrations.api.serializers import CalibrationEventSerializer


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
            'config_default_event', 'photos',
        ]
        #optional_fields = ['photos']
        deferred_fields = ('photos', )
    """
    # need a custom create() method to handle nested fields
    def create(self, validated_data):
        photo_note_data = validated_data.pop('photos')
        action = Action.objects.create(**validated_data)
        if photo_note_data:
            for photo_note in photo_note_data:
                PhotoNote.objects.create(action=action, **photo_note)
        return action
    """


class InventorySerializer(DynamicModelSerializer):
    location = DynamicRelationField('LocationSerializer', read_only=True)
    part = DynamicRelationField('PartSerializer', read_only=True)
    children = DynamicRelationField('InventorySerializer', read_only=True, many=True)
    custom_fields = serializers.SerializerMethodField('get_custom_fields')
    parent = DynamicRelationField('InventorySerializer', read_only=True)
    calibration_events = DynamicRelationField('CalibrationEventSerializer', read_only=True, many=True)

    class Meta:
        model = Inventory
        fields = [
            'id', 'serial_number', 'old_serial_number', 'part', 'location', 'revision', \
            'parent', 'children', 'build', 'assembly_part', 'assigned_destination_root', 'created_at', \
            'updated_at', 'detail', 'test_result', 'test_type', 'flag', 'time_at_sea', 'custom_fields',
            'calibration_events'
        ]

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

    def get_children(self, obj):
        # Get this item's children
        custom_fields = None
        if obj.children.exists():
            custom_fields = [child.id for child in obj.children.all()]
        return custom_fields


# Need a "sub-serializer" to handle self refernce MPTT tree structures
# If we need to embed parent/children data instead of side-loading
class InventoryTreeSerializer(InventorySerializer):
    children = DynamicRelationField('InventorySerializer', read_only=True, many=True, embed=True)
    parent = DynamicRelationField('InventorySerializer', read_only=True, embed=True)


"""
# Need a "sub-serializer" to handle self refernce MPTT tree structures
class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data
"""
