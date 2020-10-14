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

from django_filters import rest_framework as filters

from roundabout.core.api.filters import NumberInFilter
from ..models import *


class VesselFilter(filters.FilterSet):
    vessel_name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Vessel
        fields = [
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


class CruiseFilter(filters.FilterSet):
    friendly_name = filters.CharFilter(lookup_expr='icontains')
    vessel__name = filters.CharFilter(field_name='vessel__vessel_name', lookup_expr='icontains')
    vessel__in = NumberInFilter(field_name='vessel', lookup_expr='in')
    cruise_start_date = filters.DateFilter(lookup_expr='contains')
    cruise_stop_date = filters.DateFilter(lookup_expr='contains')
    cruise_start_date_range = filters.DateFromToRangeFilter(field_name='cruise_start_date')
    cruise_stop_date_range = filters.DateFromToRangeFilter(field_name='cruise_stop_date')
    location__name = filters.CharFilter(field_name='location__name', lookup_expr='icontains')
    location__in = NumberInFilter(field_name='location', lookup_expr='in')

    class Meta:
        model = Cruise
        fields = [
            'CUID',
            'vessel',
            'notes',
            'location',
            'deployments',
            'recovered_deployments',
            'inventorydeployments',
            'recovered_inventorydeployments',
        ]
