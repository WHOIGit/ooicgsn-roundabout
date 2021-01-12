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
from .serializers import BuildSerializer, DeploymentSerializer, DeploymentOmsCustomSerializer


class BuildViewSet(FlexModelViewSet):
    queryset = Build.objects.all()
    serializer_class = BuildSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = BuildFilter


class DeploymentViewSet(FlexModelViewSet):
    queryset = Deployment.objects.all()
    serializer_class = DeploymentSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = DeploymentFilter


class DeploymentOmsCustomViewSet(FlexModelViewSet):
    serializer_class = DeploymentOmsCustomSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = DeploymentOmsCustomFilter

    def get_queryset(self):
        queryset = Deployment.objects.all().prefetch_related('inventory_deployments')
        queryset = queryset.prefetch_related('inventory_deployments').select_related('build')
        return queryset
