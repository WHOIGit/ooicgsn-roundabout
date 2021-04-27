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


class LocationFilter(filters.FilterSet):
    created_at = filters.DateFilter(lookup_expr="contains")
    updated_at = filters.DateFilter(lookup_expr="contains")
    created_at__range = filters.DateFromToRangeFilter(field_name="created_at")
    updated_at__range = filters.DateFromToRangeFilter(field_name="updated_at")
    name = filters.CharFilter(lookup_expr="icontains")
    is_root = filters.BooleanFilter(field_name="parent", lookup_expr="isnull")
    has_children = filters.BooleanFilter(
        field_name="children", lookup_expr="isnull", exclude=True
    )

    class Meta:
        model = Location
        fields = [
            "parent",
            "children",
            "weight",
            "location_code",
            "root_type",
            "inventory",
            "builds",
            "deployments",
            "deployed_deployments",
        ]
