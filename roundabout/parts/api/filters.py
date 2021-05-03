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


class PartFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    part_number = filters.CharFilter(lookup_expr='icontains')
    friendly_name = filters.CharFilter(lookup_expr='icontains')
    part_type__name = filters.CharFilter(field_name='part_type__name', lookup_expr='icontains')
    unit_cost = filters.NumberFilter()
    unit_cost__gt = filters.NumberFilter(field_name='unit_cost', lookup_expr='gt')
    unit_cost__lt = filters.NumberFilter(field_name='unit_cost', lookup_expr='lt')
    refurbishment_cost = filters.NumberFilter()
    refurbishment_cost__gt = filters.NumberFilter(field_name='refurbishment_cost', lookup_expr='gt')
    refurbishment_cost__lt = filters.NumberFilter(field_name='refurbishment_cost', lookup_expr='lt')

    class Meta:
        model = Part
        fields = [
            'part_type',
            'user_defined_fields',
            'cal_dec_places',
            'part_coefficientnameevents',
            'coefficient_names',
        ]


class RevisionFilter(filters.FilterSet):
    part__name = filters.CharFilter(field_name='part__name', lookup_expr='icontains')
    part__part_number = filters.CharFilter(field_name='part__part_number', lookup_expr='icontains')
    created_at = filters.DateFilter(lookup_expr='contains')
    created_at__range = filters.DateFromToRangeFilter(field_name='created_at')
    unit_cost = filters.NumberFilter()
    unit_cost__gt = filters.NumberFilter(field_name='unit_cost', lookup_expr='gt')
    unit_cost__lt = filters.NumberFilter(field_name='unit_cost', lookup_expr='lt')
    refurbishment_cost = filters.NumberFilter()
    refurbishment_cost__gt = filters.NumberFilter(field_name='refurbishment_cost', lookup_expr='gt')
    refurbishment_cost__lt = filters.NumberFilter(field_name='refurbishment_cost', lookup_expr='lt')

    class Meta:
        model = Revision
        fields = [
            'revision_code',
            'part',
        ]


class PartTypeFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    is_root = filters.BooleanFilter(field_name='parent', lookup_expr='isnull')

    class Meta:
        model = PartType
        fields = [
            'parent', 'children', 'parts',
        ]


class DocumentationFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Documentation
        fields = [
            'doc_type', 'doc_link', 'revision',
        ]
