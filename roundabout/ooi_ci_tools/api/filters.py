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

from ..models import ReferenceDesignator
from roundabout.inventory.models import Deployment


class ArticleFilter(filters.Filter):
    def filter(self, qs, value):
        return qs.article_set.filter(name=value)


class ReferenceDesignatorFilter(filters.FilterSet):
    refdes_name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = ReferenceDesignator
        fields = [
            "instrument",
            "manufacturer",
            "model",
        ]


class CiRefDesDeploymentCustomFilter(filters.FilterSet):
    deployment_number = filters.CharFilter(lookup_expr="icontains")
    build_number = filters.CharFilter(
        field_name="build__build_number", lookup_expr="icontains"
    )
    reference_designator = filters.CharFilter(
        field_name="build__assembly_revision__assembly_parts__reference_designator__refdes_name",
        lookup_expr="exact",
    )

    class Meta:
        model = Deployment
        fields = [
            "reference_designator",
            "deployment_number",
            "build_number",
            "build",
        ]
