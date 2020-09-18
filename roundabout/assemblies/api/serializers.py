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
from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields import DynamicRelationField

from ..models import Assembly, AssemblyPart, AssemblyType, AssemblyRevision
from roundabout.parts.api.serializers import PartSerializer
from roundabout.core.api.serializers import RecursiveFieldSerializer


class AssemblyPartSerializer(DynamicModelSerializer):
    part = DynamicRelationField('PartSerializer', read_only=True, embed=True)
    parent = DynamicRelationField('AssemblyPartSerializer', read_only=True)
    #children = RecursiveFieldSerializer(many=True)
    children = DynamicRelationField('AssemblyPartSerializer', read_only=True, many=True)

    class Meta:
        model = AssemblyPart
        fields = ['id', 'part', 'parent', 'children', 'note' ]


class AssemblyTypeSerializer(DynamicModelSerializer):
    class Meta:
        model = AssemblyType
        fields = ['name']


class AssemblyRevisionSerializer(DynamicModelSerializer):
    #assembly = AssemblySerializer(read_only=True)
    assembly = DynamicRelationField('AssemblySerializer', read_only=True, embed=True)
    assembly_parts = DynamicRelationField(
        'AssemblyPartSerializer',
        read_only=True,
        many=True,
        #embed=True,
        #queryset=AssemblyPart.objects.root_nodes()
    )

    class Meta:
        model = AssemblyRevision
        fields = ['id', 'revision_code', 'revision_note', 'created_at', 'assembly', 'assembly_parts']


class AssemblySerializer(DynamicModelSerializer):
    assembly_type = DynamicRelationField('AssemblyTypeSerializer', read_only=True, embed=True)
    assembly_revisions = DynamicRelationField('AssemblyRevisionSerializer', read_only=True, many=True)

    class Meta:
        model = Assembly
        fields = ['id', 'name', 'assembly_number', 'description', 'assembly_type', 'assembly_revisions' ]
