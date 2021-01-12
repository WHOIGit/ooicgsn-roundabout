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

from roundabout.locations.models import Location
from ..models import Vessel, Cruise

API_VERSION = 'api_v1'

class VesselSerializer(serializers.HyperlinkedModelSerializer, FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':vessels-detail',
        lookup_field = 'pk',
    )
    cruises = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':cruises-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )

    class Meta:
        model = Vessel
        fields = [
            'id',
            'url',
            'prefix',
            'vessel_designation',
            'vessel_name',
            'ICES_code',
            'operator',
            'call_sign',
            'MMSI_number',
            'IMO_number',
            'length',
            'max_speed',
            'max_draft',
            'designation',
            'active',
            'R2R',
            'notes',
            'cruises',
        ]

        expandable_fields = {
            'cruises': ('roundabout.cruises.api.serializers.CruiseSerializer', {'many': True})
        }


class CruiseSerializer(serializers.HyperlinkedModelSerializer, FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':cruises-detail',
        lookup_field = 'pk',
    )
    vessel = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':vessels-detail',
        lookup_field = 'pk',
        queryset = Vessel.objects
    )
    deployments = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':deployments-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )
    recovered_deployments = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':deployments-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )
    inventorydeployments = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':inventory-deployments-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )
    recovered_inventorydeployments = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':inventory-deployments-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )
    location = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':locations-detail',
        lookup_field = 'pk',
        queryset = Location.objects
    )

    class Meta:
        model = Cruise
        fields = [
            'id',
            'url',
            'CUID',
            'friendly_name',
            'vessel',
            'cruise_start_date',
            'cruise_stop_date',
            'notes',
            'location',
            'deployments',
            'recovered_deployments',
            'inventorydeployments',
            'recovered_inventorydeployments',
        ]

        expandable_fields = {
            'vessel': 'roundabout.cruises.api.serializers.VesselSerializer',
            'location': 'roundabout.locations.api.serializers.LocationSerializer',
            'deployments': ('roundabout.builds.api.serializers.DeploymentSerializer', {'many': True}),
            'recovered_deployments': ('roundabout.builds.api.serializers.DeploymentSerializer', {'many': True})
        }
