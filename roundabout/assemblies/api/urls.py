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
from dynamic_rest.routers import DynamicRouter
from .views import AssemblyViewSet, AssemblyRevisionViewSet, AssemblyPartViewSet

# Create a router and register our viewsets with it.
router = DynamicRouter()
router.register(r'assemblies', AssemblyViewSet, 'assemblies' )
router.register(r'assembly_revisions', AssemblyRevisionViewSet, 'assembly_revisions' )
router.register(r'assembly_parts', AssemblyPartViewSet, 'assembly_parts' )

urlpatterns = [
    path('', include(router.urls) ),
]
