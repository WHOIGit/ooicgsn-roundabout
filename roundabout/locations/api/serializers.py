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
from ..models import Location

API_VERSION = 'api_v1'

class LocationSerializer(serializers.HyperlinkedModelSerializer, FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':locations-detail',
        lookup_field = 'pk',
    )
    parent = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':locations-detail',
        lookup_field = 'pk',
        queryset = Location.objects
    )
    children = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':locations-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )

    class Meta:
        model = Location
        fields = ['id', 'url', 'name', 'parent', 'children', 'weight',
            'location_type', 'location_id', 'root_type', 'created_at',
        ]

        expandable_fields = {
            'parent': 'roundabout.locations.api.serializers.LocationSerializer',
            'children': ('roundabout.locations.api.serializers.LocationSerializer', {'many': True})
        }
