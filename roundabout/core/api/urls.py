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
from roundabout.parts.api.views import PartViewSet, PartTypeViewSet, RevisionViewSet, DocumentationViewSet
from roundabout.userdefinedfields.api.views import FieldViewSet, FieldValueViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'inventory', InventoryViewSet, 'inventory' )
router.register(r'actions', ActionViewSet, 'actions' )
router.register(r'photos', PhotoNoteViewSet, 'photos' )

router.register(r'assembly-templates/assemblies', AssemblyViewSet, 'assembly-templates/assemblies' )
router.register(r'assembly-templates/assembly-revisions', AssemblyRevisionViewSet, 'assembly-templates/assembly-revisions' )
router.register(r'assembly-templates/assembly-parts', AssemblyPartViewSet, 'assembly-templates/assembly-parts' )

router.register(r'calibrations/calibration-events', CalibrationEventViewSet, 'calibrations/calibration-events' )
router.register(r'calibrations/coefficent-name-events', CoefficientNameEventViewSet, 'calibrations/coefficent-name-events' )

router.register(r'locations', LocationViewSet, 'locations' )

router.register(r'part-templates/parts', PartViewSet, 'part-templates/parts' )
router.register(r'part-templates/part-types', PartTypeViewSet, 'part-templates/part-types' )
router.register(r'part-templates/revisions', RevisionViewSet, 'part-templates/revisions' )
router.register(r'part-templates/documents', DocumentationViewSet, 'part-templates/documents' )

router.register(r'userdefined-fields/fields', FieldViewSet, 'userdefined-fields/fields' )
router.register(r'userdefined-fields/field-values', FieldValueViewSet, 'userdefined-fields/field-values' )

app_name = 'api_v1'
urlpatterns = [
    path('', include(router.urls) ),
]
