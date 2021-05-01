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
from rest_framework.decorators import action
from rest_framework.response import Response

from roundabout.core.api.views import FlexModelViewSet
from roundabout.inventory.utils import _create_action_history
from roundabout.inventory.models import Action
from .filters import *
from .serializers import LocationSerializer


class LocationViewSet(FlexModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Location.objects.all()
    filterset_class = LocationFilter

    def save_with_action_history(self, serializer, action_type, action_date=None):
        print(serializer.validated_data)
        obj = serializer.save()
        _create_action_history(
            obj,
            action_type,
            self.request.user,
            action_date=action_date,
        )

    def perform_create(self, serializer):
        action_date = serializer.validated_data["created_at"]
        self.save_with_action_history(serializer, Action.ADD, action_date)

    def perform_update(self, serializer):
        self.save_with_action_history(serializer, Action.UPDATE)

    @action(detail=True, methods=["post"], url_path="some-action")
    def some_action(self, request, pk=None):
        location = self.get_object()
        print(location)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            location.name(serializer.validated_data["name"])
            location.save()
            return Response({"status": "Action Complete"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
