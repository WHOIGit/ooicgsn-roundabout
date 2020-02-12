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

from rest_framework import serializers

from ..models import Assembly, AssemblyPart, AssemblyType
from roundabout.parts.api.serializers import PartSerializer


class AssemblyPartSerializer(serializers.ModelSerializer):
    part = PartSerializer(read_only=True)

    class Meta:
        model = AssemblyPart
        fields = ['id', 'part', 'parent', 'note', 'order' ]

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary prefetching of data. """
        queryset = queryset.select_related('part')

        return queryset


class AssemblyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssemblyType
        fields = ['name']


class AssemblySerializer(serializers.ModelSerializer):
    assembly_parts = AssemblyPartSerializer(many=True, read_only=True)
    assembly_type = AssemblyTypeSerializer(read_only=True)

    class Meta:
        model = Assembly
        fields = ['id', 'name', 'assembly_number', 'description', 'assembly_type', 'assembly_parts' ]

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary prefetching of data. """
        queryset = queryset.prefetch_related('assembly_parts')

        return queryset
