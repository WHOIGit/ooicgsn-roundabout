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
from rest_flex_fields import FlexFieldsModelSerializer

from ..models import Assembly, AssemblyPart, AssemblyType, AssemblyRevision
from roundabout.parts.models import Part
from roundabout.parts.api.serializers import PartSerializer
from roundabout.core.api.serializers import RecursiveFieldSerializer

API_VERSION = 'api_v1'

class AssemblyTypeSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = AssemblyType
        fields = ['name']


class AssemblySerializer(FlexFieldsModelSerializer):
    class Meta:
        model = Assembly
        fields = ['id', 'name', 'assembly_number', 'description', 'assembly_type', 'assembly_revisions' ]

        expandable_fields = {
            'assembly_type': 'roundabout.assemblies.api.serializers.AssemblyTypeSerializer',
            'assembly_revisions': ('roundabout.assemblies.api.serializers.AssemblyRevisionSerializer', {'many': True})
        }


class AssemblyRevisionSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = AssemblyRevision
        fields = ['id', 'revision_code', 'revision_note', 'created_at', 'assembly', 'assembly_parts']

        expandable_fields = {
            'assembly': 'roundabout.assemblies.api.serializers.AssemblySerializer',
            'assembly_parts': ('roundabout.assemblies.api.serializers.AssemblyPartSerializer', {'many': True})
        }


class AssemblyPartSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':assembly-templates/assembly-parts-detail',
        lookup_field = 'pk',
    )
    parent = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':assembly-templates/assembly-parts-detail',
        lookup_field = 'pk',
        queryset = AssemblyPart.objects
    )
    children = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':assembly-templates/assembly-parts-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )
    part = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':part-templates/parts-detail',
        lookup_field = 'pk',
        queryset = Part.objects
    )

    class Meta:
        model = AssemblyPart
        fields = ['id', 'url', 'part', 'parent', 'children', 'note', ]

        expandable_fields = {
            'part': PartSerializer,
            'parent': 'roundabout.assemblies.api.serializers.AssemblyPartSerializer',
            'children': ('roundabout.assemblies.api.serializers.AssemblyPartSerializer', {'many': True})
        }
