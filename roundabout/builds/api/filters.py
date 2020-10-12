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
from roundabout.core.api.filters import NumberInFilter


class BuildFilter(filters.FilterSet):
    build_number = filters.CharFilter(lookup_expr='icontains')
    assembly__name = filters.CharFilter(field_name='assembly__name', lookup_expr='icontains')
    assembly__in = NumberInFilter(field_name='assembly', lookup_expr='in')
    assembly_revision__revision_code = filters.CharFilter(field_name='assembly_revision__revision_code', lookup_expr='icontains')
    location__name = filters.CharFilter(field_name='location__name', lookup_expr='icontains')
    location__in = NumberInFilter(field_name='location', lookup_expr='in')
    has_time_in_field = filters.BooleanFilter(field_name='time_at_sea', method='filter_time_in_field')

    class Meta:
        model = Build
        fields = [
            'assembly',
            'assembly_revision',
            'is_deployed',
            'inventory',
            'location',
            'flag',
        ]

    def filter_time_in_field(self, queryset, name, value):
        # construct the full lookup expression.
        lookup = '__'.join([name, 'isnull'])
        return queryset.filter(**{lookup: False})

        # alternatively, you could opt to hardcode the lookup. e.g.,
        # return queryset.filter(published_on__isnull=False)
