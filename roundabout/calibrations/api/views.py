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

from rest_framework import generics, filters, viewsets
from rest_framework.permissions import IsAuthenticated

from roundabout.core.api.views import FlexModelViewSet
from ..models import *
from .serializers import *
from .filters import *


class CalibrationEventViewSet(FlexModelViewSet):
    serializer_class = CalibrationEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = CalibrationEvent.objects.all()
    filterset_class = CalibrationEventFilter


class CoefficientNameEventViewSet(FlexModelViewSet):
    serializer_class = CoefficientNameEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = CoefficientNameEvent.objects.all()
    filterset_class = CoefficientNameEventFilter


class CoefficientNameViewSet(FlexModelViewSet):
    serializer_class = CoefficientNameSerializer
    permission_classes = (IsAuthenticated,)
    queryset = CoefficientName.objects.all()
    filterset_class = CoefficientNameFilter


class CoefficientValueSetViewSet(FlexModelViewSet):
    serializer_class = CoefficientValueSetSerializer
    permission_classes = (IsAuthenticated,)
    queryset = CoefficientValueSet.objects.all()
    filterset_class = CoefficientValueSetFilter


class CoefficientValueViewSet(FlexModelViewSet):
    serializer_class = CoefficientValueSerializer
    permission_classes = (IsAuthenticated,)
    queryset = CoefficientValue.objects.all()
    filterset_class = CoefficientValueFilter
