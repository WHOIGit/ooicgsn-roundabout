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
from roundabout.inventory.models import InventoryDeployment
from ..models import ReferenceDesignator, ReferenceDesignatorEvent
from .filters import (
    ReferenceDesignatorFilter,
    CiRefDesDeploymentCustomFilter,
)
from .serializers import (
    ReferenceDesignatorSerializer,
    ReferenceDesignatorEventSerializer,
    CiRefDesDeploymentCustomSerializer,
)


class ReferenceDesignatorViewSet(FlexModelViewSet):
    serializer_class = ReferenceDesignatorSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ReferenceDesignator.objects.all()
    filterset_class = ReferenceDesignatorFilter


class ReferenceDesignatorEventViewSet(FlexModelViewSet):
    serializer_class = ReferenceDesignatorEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ReferenceDesignatorEvent.objects.all()


class CiRefDesDeploymentCustomViewSet(FlexModelViewSet):
    serializer_class = CiRefDesDeploymentCustomSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = CiRefDesDeploymentCustomFilter

    def get_queryset(self):
        queryset = InventoryDeployment.objects.all()
        queryset = queryset.select_related("assembly_part")
        return queryset
