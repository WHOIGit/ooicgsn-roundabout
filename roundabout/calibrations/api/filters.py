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


class CalibrationEventFilter(filters.FilterSet):

    class Meta:
        model = CalibrationEvent
        fields = [
            'user_draft',
            'user_approver',
            'inventory',
            'deployment',
            'approved',
        ]


class CoefficientNameEventFilter(filters.FilterSet):

    class Meta:
        model = CoefficientNameEvent
        fields = [
            'user_draft',
            'user_approver',
            'part',
            'approved',
            'detail',
            'coefficient_names'
        ]


class CoefficientNameFilter(filters.FilterSet):
    calibration_name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = CoefficientName
        fields = [
            'value_set_type',
            'sigfig_override',
            'part',
            'coeff_name_event',
            'coefficient_value_sets',
        ]


class CoefficientValueSetFilter(filters.FilterSet):
    value_set = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = CoefficientValueSet
        fields = [
            'coefficient_name',
            'calibration_event',
            'coefficient_values',
        ]


class CoefficientValueFilter(filters.FilterSet):
    value = filters.CharFilter(lookup_expr='icontains')
    original_value = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = CoefficientValue
        fields = [
            'value',
            'original_value',
            'notation_format',
            'sigfig',
            'row',
            'coeff_value_set',
        ]
