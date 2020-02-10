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

from django.urls import path

from . import views

app_name = 'locations'
urlpatterns = [
    path('', view=views.LocationsHomeView.as_view(), name='locations_home'),
    path('<int:pk>/', view=views.LocationsDetailView.as_view(), name='locations_detail'),
    #path('<int:pk>/<int:current_location>/', view=views.LocationsDetailView.as_view(), name='locations_detail'),
    path('add/', view=views.LocationsCreateView.as_view(), name='locations_add'),
    path('edit/<int:pk>/', view=views.LocationsUpdateView.as_view(), name='locations_update'),
    #path('edit/<int:pk>/<int:current_location>/', view=views.LocationsUpdateView.as_view(), name='locations_update'),
    path('delete/<int:pk>/', view=views.LocationsDeleteView.as_view(), name='locations_delete'),
    # AJAX paths
    path('ajax/load-navtree/', views.load_locations_navtree, name='ajax_load_locations_navtree'),
    path('ajax/detail/<int:pk>/', view=views.LocationsAjaxDetailView.as_view(), name='ajax_location_detail'),
    path('ajax/edit/<int:pk>/', view=views.LocationsAjaxUpdateView.as_view(), name='ajax_location_update'),
    path('ajax/add/', view=views.LocationsAjaxCreateView.as_view(), name='ajax_location_add'),
    path('ajax/delete/<int:pk>/', view=views.LocationsAjaxDeleteView.as_view(), name='ajax_location_delete'),
]
