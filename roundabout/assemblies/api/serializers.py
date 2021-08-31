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

from rest_flex_fields import FlexFieldsModelSerializer
from rest_framework import serializers
from rest_framework.reverse import reverse

from roundabout.parts.api.serializers import PartSerializer
from roundabout.parts.models import Part
from roundabout.ooi_ci_tools.models import ReferenceDesignator
from ..models import Assembly, AssemblyPart, AssemblyType, AssemblyRevision

API_VERSION = "api_v1"


class AssemblyTypeSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":assembly-templates/assembly-types-detail",
        lookup_field="pk",
    )
    assemblies = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assemblies-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )

    class Meta:
        model = AssemblyType
        fields = ["id", "url", "name", "assemblies"]

        expandable_fields = {
            "assemblies": (
                "roundabout.assemblies.api.serializers.AssemblySerializer",
                {"many": True},
            )
        }


class AssemblySerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":assembly-templates/assemblies-detail",
        lookup_field="pk",
    )
    assembly_revisions = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assembly-revisions-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )
    assembly_type = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assembly-types-detail",
        lookup_field="pk",
        queryset=AssemblyType.objects,
    )

    class Meta:
        model = Assembly
        fields = [
            "id",
            "url",
            "name",
            "assembly_number",
            "description",
            "assembly_type",
            "assembly_revisions",
        ]

        expandable_fields = {
            "assembly_type": "roundabout.assemblies.api.serializers.AssemblyTypeSerializer",
            "assembly_revisions": (
                "roundabout.assemblies.api.serializers.AssemblyRevisionSerializer",
                {"many": True},
            ),
        }


class AssemblyRevisionSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":assembly-templates/assembly-revisions-detail",
        lookup_field="pk",
    )
    assembly_parts_roots = serializers.SerializerMethodField("get_assembly_parts_roots")
    assembly_parts = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assembly-parts-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )
    assembly = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assemblies-detail",
        lookup_field="pk",
        queryset=Assembly.objects,
    )

    class Meta:
        model = AssemblyRevision
        fields = [
            "id",
            "url",
            "revision_code",
            "revision_note",
            "created_at",
            "assembly",
            "assembly_parts_roots",
            "assembly_parts",
        ]

        expandable_fields = {
            "assembly": "roundabout.assemblies.api.serializers.AssemblySerializer",
            "assembly_parts": (
                "roundabout.assemblies.api.serializers.AssemblyPartSerializer",
                {"many": True},
            ),
        }

    def get_assembly_parts_roots(self, obj):
        # Get all the Root AssemblyParts only
        assembly_parts = obj.assembly_parts.filter(parent__isnull=True)
        assembly_parts_list = [
            reverse(
                API_VERSION + ":assembly-templates/assembly-parts-detail",
                kwargs={"pk": assembly_part.id},
                request=self.context["request"],
            )
            for assembly_part in assembly_parts
        ]
        return assembly_parts_list


class AssemblyPartSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":assembly-templates/assembly-parts-detail",
        lookup_field="pk",
    )
    parent = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assembly-parts-detail",
        lookup_field="pk",
        queryset=AssemblyPart.objects,
        allow_null=True,
    )
    children = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assembly-parts-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )
    assembly_revision = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-templates/assembly-revisions-detail",
        lookup_field="pk",
        queryset=AssemblyRevision.objects,
    )
    part = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":part-templates/parts-detail",
        lookup_field="pk",
        queryset=Part.objects,
    )
    part_name = serializers.CharField(source="order")
    reference_designator = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":reference-designators-detail",
        lookup_field="pk",
        queryset=ReferenceDesignator.objects,
    )
    assemblypart_configdefaultevents = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":configs-constants/config-default-events-detail",
        many=True,
        read_only=True,
        lookup_field="pk",
    )

    class Meta:
        model = AssemblyPart
        fields = [
            "id",
            "url",
            "assembly_revision",
            "part_name",
            "part",
            "reference_designator",
            "parent",
            "children",
            "note",
            "order",
            "assemblypart_configdefaultevents",
        ]

        expandable_fields = {
            "part": PartSerializer,
            "reference_designator": "roundabout.ooi_ci_tools.api.serializers.ReferenceDesignatorSerializer",
            "assembly_revision": "roundabout.assemblies.api.serializers.AssemblyRevisionSerializer",
            "parent": "roundabout.assemblies.api.serializers.AssemblyPartSerializer",
            "children": (
                "roundabout.assemblies.api.serializers.AssemblyPartSerializer",
                {"many": True},
            ),
            "assemblypart_configdefaultevents": (
                "roundabout.configs_constants.api.serializers.ConfigDefaultEventSerializer",
                {"many": True},
            ),
        }
