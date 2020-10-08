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
from ..models import *
from .serializers import *


class ConfigEventViewSet(viewsets.ModelViewSet):
    serializer_class = ConfigEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigEvent.objects.all()


class ConfigNameEventViewSet(viewsets.ModelViewSet):
    serializer_class = ConfigNameEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigNameEvent.objects.all()


class ConfigNameViewSet(viewsets.ModelViewSet):
    serializer_class = ConfigNameSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigName.objects.all()


class ConfigValueViewSet(viewsets.ModelViewSet):
    serializer_class = ConfigValueSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigValue.objects.all()


class ConstDefaultEventViewSet(viewsets.ModelViewSet):
    serializer_class = ConstDefaultEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConstDefaultEvent.objects.all()


class ConstDefaultViewSet(viewsets.ModelViewSet):
    serializer_class = ConstDefaultSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConstDefault.objects.all()


class ConfigDefaultEventViewSet(viewsets.ModelViewSet):
    serializer_class = ConfigDefaultEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigDefaultEvent.objects.all()


class ConfigDefaultViewSet(viewsets.ModelViewSet):
    serializer_class = ConfigDefaultSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ConfigDefault.objects.all()
