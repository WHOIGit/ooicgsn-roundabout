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


class InventoryFilter(filters.FilterSet):
    created_at = filters.DateFilter(lookup_expr='contains')
    updated_at = filters.DateFilter(lookup_expr='contains')
    created_at__range = filters.DateFromToRangeFilter(field_name='created_at')
    updated_at__range = filters.DateFromToRangeFilter(field_name='updated_at')
    serial_number = filters.CharFilter(lookup_expr='icontains')
    old_serial_number = filters.CharFilter(lookup_expr='icontains')
    part__name = filters.CharFilter(field_name='part__name', lookup_expr='icontains')
    part__number = filters.CharFilter(field_name='part__part_number', lookup_expr='icontains')
    field_value = filters.CharFilter(field_name='fieldvalues__field_value', lookup_expr='icontains')
    field_name = filters.CharFilter(field_name='fieldvalues__field__field_name', lookup_expr='icontains')
    build__isnull = filters.BooleanFilter(field_name='build', lookup_expr='isnull')
    parent__isnull = filters.BooleanFilter(field_name='parent', lookup_expr='isnull')
    children__isnull = filters.BooleanFilter(field_name='children', lookup_expr='isnull')
    is_root = filters.BooleanFilter(field_name='parent', lookup_expr='isnull')
    has_children = filters.BooleanFilter(field_name='children', lookup_expr='isnull', exclude=True)
    inventory_calibrationevents__isnull = filters.BooleanFilter(field_name='inventory_calibrationevents', lookup_expr='isnull')
    inventory_deployments__isnull = filters.BooleanFilter(field_name='inventory_deployments', lookup_expr='isnull')

    #is_deployed = filters.BooleanFilter(field_name='time_at_sea', method='filter_is_deployed')

    class Meta:
        model = Inventory
        fields = [
            'part',
            'location',
            'revision',
            'parent',
            'children',
            'build',
            'test_result',
            'test_type',
            'flag',
        ]


class ActionFilter(filters.FilterSet):
    created_at = filters.DateFilter(lookup_expr='contains')
    created_at__range = filters.DateFromToRangeFilter(field_name='created_at')
    detail = filters.CharFilter(lookup_expr='icontains')
    inventory__serial_number = filters.CharFilter(field_name='inventory__serial_number', lookup_expr='icontains')
    user__username = filters.CharFilter(field_name='user__username', lookup_expr='icontains')

    class Meta:
        model = Action
        fields = [
            'action_type',
            'object_type',
            'inventory',
            'location',
            'deployment',
            'inventory_deployment',
            'deployment_type',
            'detail',
            'user',
            'build',
            'parent',
            'cruise',
            'latitude',
            'longitude',
            'depth',
            'calibration_event',
            'const_default_event',
            'config_event',
            'config_default_event',
            'coefficient_name_event',
            'config_name_event',
        ]


class InventoryDeploymentFilter(filters.FilterSet):
    deployment_start_date = filters.DateFilter(lookup_expr='contains')
    deployment_burnin_date = filters.DateFilter(lookup_expr='contains')
    deployment_to_field_date = filters.DateFilter(lookup_expr='contains')
    deployment_recovery_date = filters.DateFilter(lookup_expr='contains')
    deployment_retire_date = filters.DateFilter(lookup_expr='contains')
    deployment_year = filters.NumberFilter(field_name='deployment_to_field_date', lookup_expr='year')

    class Meta:
        model = InventoryDeployment
        fields = [
            'deployment',
            'inventory',
            'cruise_deployed',
            'cruise_recovered',
            'current_status',
        ]
