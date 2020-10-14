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

from ..models import *
from roundabout.core.api.filters import NumberInFilter


class ConfigEventFilter(filters.FilterSet):
    created_at = filters.DateFilter(lookup_expr='contains')
    updated_at = filters.DateFilter(lookup_expr='contains')
    configuration_date = filters.DateFilter(lookup_expr='contains')
    created_at_range = filters.DateFromToRangeFilter(field_name='created_at')
    updated_at_range = filters.DateFromToRangeFilter(field_name='updated_at')
    configuration_date_range = filters.DateFromToRangeFilter(field_name='configuration_date')

    class Meta:
        model = ConfigEvent
        fields = [
            'user_draft',
            'user_approver',
            'inventory',
            'deployment',
            'approved',
            'detail',
            'config_type',
            'config_values',
        ]


class ConfigNameEventFilter(filters.FilterSet):
    created_at = filters.DateFilter(lookup_expr='contains')
    updated_at = filters.DateFilter(lookup_expr='contains')
    created_at_range = filters.DateFromToRangeFilter(field_name='created_at')
    updated_at_range = filters.DateFromToRangeFilter(field_name='updated_at')

    class Meta:
        model = ConfigNameEvent
        fields = [
            'user_draft',
            'user_approver',
            'part',
            'approved',
            'detail',
            'config_names'
        ]


class ConfigNameFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    created_at = filters.DateFilter(lookup_expr='contains')
    created_at_range = filters.DateFromToRangeFilter(field_name='created_at')

    class Meta:
        model = ConfigName
        fields = [
            'config_type',
            'deprecated',
            'part',
            'include_with_calibrations',
            'config_name_event',
            'config_values',
            'constant_defaults',
            'config_defaults',
        ]


class ConfigValueFilter(filters.FilterSet):
    config_value = filters.CharFilter(lookup_expr='icontains')
    created_at = filters.DateFilter(lookup_expr='contains')
    created_at_range = filters.DateFromToRangeFilter(field_name='created_at')

    class Meta:
        model = ConfigValue
        fields = [
            'notes',
            'config_name',
            'config_event',
        ]
