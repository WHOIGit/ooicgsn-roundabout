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

from rest_framework.permissions import IsAuthenticated

from roundabout.core.api.views import FlexModelViewSet
from .filters import *
from .serializers import PartSerializer, PartTypeSerializer, RevisionSerializer, DocumentationSerializer


class PartTypeViewSet(FlexModelViewSet):
    serializer_class = PartTypeSerializer
    permission_classes = (IsAuthenticated,)
    queryset = PartType.objects.all()
    filterset_class = PartTypeFilter


class PartViewSet(FlexModelViewSet):
    serializer_class = PartSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Part.objects.all()
    filterset_class = PartFilter


class RevisionViewSet(FlexModelViewSet):
    serializer_class = RevisionSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Revision.objects.all()
    filterset_class = RevisionFilter


class DocumentationViewSet(FlexModelViewSet):
    serializer_class = DocumentationSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Documentation.objects.all()
    filterset_class = DocumentationFilter
