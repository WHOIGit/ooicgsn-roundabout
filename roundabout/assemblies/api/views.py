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

from django.db.models import Prefetch
from rest_framework.permissions import IsAuthenticated

from roundabout.core.api.views import FlexModelViewSet
from .filters import *
from .serializers import *


class AssemblyViewSet(FlexModelViewSet):
    serializer_class = AssemblySerializer
    permission_classes = (IsAuthenticated,)
    queryset = Assembly.objects.all()
    filterset_class = AssemblyFilter


class AssemblyTypeViewSet(FlexModelViewSet):
    serializer_class = AssemblyTypeSerializer
    permission_classes = (IsAuthenticated,)
    queryset = AssemblyType.objects.all()


class AssemblyRevisionViewSet(FlexModelViewSet):
    serializer_class = AssemblyRevisionSerializer
    permission_classes = (IsAuthenticated,)
    queryset = AssemblyRevision.objects.prefetch_related(
        Prefetch('assembly_parts', queryset=AssemblyPart.objects.order_by('-parent_id'))
    )
    filterset_class = AssemblyRevisionFilter


class AssemblyPartViewSet(FlexModelViewSet):
    serializer_class = AssemblyPartSerializer
    permission_classes = (IsAuthenticated,)
    queryset = AssemblyPart.objects.all()
    filterset_class = AssemblyPartFilter
