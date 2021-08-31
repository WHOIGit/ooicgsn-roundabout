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

from ..models import ReferenceDesignator
from roundabout.assemblies.models import AssemblyPart

API_VERSION = "api_v1"


class ReferenceDesignatorSerializer(FlexFieldsModelSerializer):
    id = serializers.ReadOnlyField()
    url = serializers.HyperlinkedIdentityField(
        view_name=API_VERSION + ":reference-designators-detail",
        lookup_field="pk",
    )
    assembly_part = serializers.HyperlinkedRelatedField(
        view_name=API_VERSION + ":assembly-parts-detail",
        lookup_field="pk",
        queryset=AssemblyPart.objects,
        required=False,
        allow_null=True,
        default=None,
    )

    class Meta:
        model = ReferenceDesignator
        fields = [
            "id",
            "url",
            "refdes_name",
            "assembly_part",
            "toc_l1",
            "toc_l2",
            "toc_l3",
            "instrument",
            "manufacturer",
            "model",
            "min_depth",
            "max_depth",
        ]

        expandable_fields = {
            "assembly_part": "roundabout.assemblies.api.serializers.AssemblyPartSerializer",
        }
