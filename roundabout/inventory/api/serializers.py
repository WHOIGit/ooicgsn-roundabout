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

from ..models import Inventory, Action
from roundabout.locations.api.serializers import LocationSerializer
from roundabout.parts.api.serializers import PartSerializer


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = '__all__'

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary prefetching of data. """
        queryset = queryset.select_related('location', 'inventory', 'build')
        #queryset = queryset.prefetch_related('fieldvalues')
        return queryset


class InventorySerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    part = PartSerializer(read_only=True)
    custom_fields = serializers.SerializerMethodField('get_custom_fields')

    class Meta:
        model = Inventory
        fields = ['id', 'serial_number', 'part', 'location', 'custom_fields' ]

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

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary prefetching of data. """
        queryset = queryset.select_related('location').select_related('part')
        queryset = queryset.prefetch_related('fieldvalues')
        return queryset
