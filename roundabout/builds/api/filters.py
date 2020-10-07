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

from ..models import Build

class BuildFilter(filters.FilterSet):
    build_number = filters.CharFilter(lookup_expr='icontains')
    location__name = filters.CharFilter(field_name='location__name', lookup_expr='icontains')
    assembly__name = filters.CharFilter(field_name='assembly__name', lookup_expr='icontains')

    class Meta:
        model = Build
        """
        fields = {
            'build_number': ['exact', 'icontains',],
            'location': ['exact', ],
            'location__name': ['exact', 'icontains',],
            'assembly__name': ['exact', 'icontains',],
        }
        """
        fields = ['assembly', 'is_deployed', 'inventory', 'location']
