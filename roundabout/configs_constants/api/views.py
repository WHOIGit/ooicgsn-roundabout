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


class ConfigEventViewSet(FlexModelViewSet):
    serializer_class = ConfigEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigEvent.objects.all()
    filterset_class = ConfigEventFilter


class ConfigNameEventViewSet(FlexModelViewSet):
    serializer_class = ConfigNameEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigNameEvent.objects.all()
    filterset_class = ConfigNameEventFilter


class ConfigNameViewSet(FlexModelViewSet):
    serializer_class = ConfigNameSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigName.objects.all()
    filterset_class = ConfigNameFilter


class ConfigValueViewSet(FlexModelViewSet):
    serializer_class = ConfigValueSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigValue.objects.all()
    filterset_class = ConfigValueFilter


class ConstDefaultEventViewSet(FlexModelViewSet):
    serializer_class = ConstDefaultEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConstDefaultEvent.objects.all()
    filterset_class = ConstDefaultEventFilter


class ConstDefaultViewSet(FlexModelViewSet):
    serializer_class = ConstDefaultSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConstDefault.objects.all()
    filterset_class = ConstDefaultFilter


class ConfigDefaultEventViewSet(FlexModelViewSet):
    serializer_class = ConfigDefaultEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigDefaultEvent.objects.all()
    filterset_class = ConfigDefaultEventFilter


class ConfigDefaultViewSet(FlexModelViewSet):
    serializer_class = ConfigDefaultSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigDefault.objects.all()
    filterset_class = ConfigDefaultFilter
