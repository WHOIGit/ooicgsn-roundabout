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

from rest_framework import generics, viewsets, filters
from rest_framework.permissions import IsAuthenticated

from roundabout.core.api.views import FlexModelViewSet
from ..models import Inventory, InventoryDeployment, Action, PhotoNote
from .serializers import InventorySerializer, InventoryDeploymentSerializer, ActionSerializer, PhotoNoteSerializer
from .filters import *

class InventoryViewSet(FlexModelViewSet):
    serializer_class = InventorySerializer
    permission_classes = (IsAuthenticated,)
    queryset = Inventory.objects.all()
    filterset_class = InventoryFilter


class InventoryDeploymentViewSet(FlexModelViewSet):
    serializer_class = InventoryDeploymentSerializer
    permission_classes = (IsAuthenticated,)
    queryset = InventoryDeployment.objects.all()
    filterset_class = InventoryDeploymentFilter


class ActionViewSet(FlexModelViewSet):
    serializer_class = ActionSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Action.objects.all()
    filterset_class = ActionFilter


class PhotoNoteViewSet(viewsets.ModelViewSet):
    serializer_class = PhotoNoteSerializer
    permission_classes = (IsAuthenticated,)
    queryset = PhotoNote.objects.all()
