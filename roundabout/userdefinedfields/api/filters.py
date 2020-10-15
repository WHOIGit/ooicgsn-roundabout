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


class FieldFilter(filters.FilterSet):
    created_at = filters.DateFilter(lookup_expr='contains')
    updated_at = filters.DateFilter(lookup_expr='contains')
    created_at_range = filters.DateFromToRangeFilter(field_name='created_at')
    updated_at_range = filters.DateFromToRangeFilter(field_name='updated_at')
    field_name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Field
        fields = [
            'field_type',
            'field_default_value',
            'global_for_part_types',
            'created_at',
            'updated_at',
            'parts',
        ]


class FieldValueFilter(filters.FilterSet):
    created_at = filters.DateFilter(lookup_expr='contains')
    updated_at = filters.DateFilter(lookup_expr='contains')
    created_at_range = filters.DateFromToRangeFilter(field_name='created_at')
    updated_at_range = filters.DateFromToRangeFilter(field_name='updated_at')
    field__field_name = filters.CharFilter(field_name='field_name', lookup_expr='icontains')
    user__username = filters.CharFilter(field_name='user__username', lookup_expr='icontains')

    class Meta:
        model = FieldValue
        fields = [
            'field_value',
            'field',
            'inventory',
            'part',
            'user',
            'is_current',
            'is_default_value',
        ]
