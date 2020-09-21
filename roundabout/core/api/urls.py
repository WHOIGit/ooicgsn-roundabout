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

from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from roundabout.inventory.api.views import InventoryViewSet, ActionViewSet, PhotoNoteViewSet
from roundabout.assemblies.api.views import AssemblyViewSet, AssemblyRevisionViewSet, AssemblyPartViewSet
from roundabout.calibrations.api.views import CalibrationEventViewSet, CoefficientNameEventViewSet
from roundabout.locations.api.views import LocationViewSet
from roundabout.parts.api.views import PartViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'inventory', InventoryViewSet, 'inventory' )
router.register(r'actions', ActionViewSet, 'actions' )
router.register(r'photos', PhotoNoteViewSet, 'photos' )

router.register(r'assemblies', AssemblyViewSet, 'assemblies' )
router.register(r'assembly_revisions', AssemblyRevisionViewSet, 'assembly_revisions' )
router.register(r'assembly_parts', AssemblyPartViewSet, 'assembly_parts' )

router.register(r'calibrations/calibration_events', CalibrationEventViewSet, 'calibrations/calibration_events' )
router.register(r'calibrations/coefficent_name_events', CoefficientNameEventViewSet, 'calibrations/coefficent_name_events' )

router.register(r'locations', LocationViewSet, 'locations' )

router.register(r'parts', PartViewSet, 'parts' )

app_name = 'api_v1'
urlpatterns = [
    path('', include(router.urls) ),
]
