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

from ..models import Assembly, AssemblyRevision, AssemblyPart
from roundabout.core.api.filters import NumberInFilter


class AssemblyFilter(filters.FilterSet):
    assembly_number = filters.CharFilter(lookup_expr='icontains')
    name = filters.CharFilter(lookup_expr='icontains')
    assembly_type__name = NumberInFilter(field_name='assembly_type__name', lookup_expr='icontains')

    class Meta:
        model = Assembly
        fields = [
            'assembly_type',
            'assembly_revisions',
        ]


class AssemblyRevisionFilter(filters.FilterSet):
    assembly__name = filters.CharFilter(field_name='assembly__name', lookup_expr='icontains')
    revision_code = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = AssemblyRevision
        fields = [
            'assembly',
        ]


class AssemblyPartFilter(filters.FilterSet):
    assembly_revision__revision_code = filters.CharFilter(field_name='assembly_revision__revision_code', lookup_expr='icontains')
    part__name = filters.CharFilter(field_name='part__name', lookup_expr='icontains')
    part__number = filters.CharFilter(field_name='part__number', lookup_expr='icontains')

    class Meta:
        model = AssemblyPart
        fields = [
            'part',
            'assembly_revision',
        ]
