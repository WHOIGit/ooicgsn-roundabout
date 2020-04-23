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

app_name = 'cruises'
urlpatterns = [
    # Cruises
    path('', view=views.CruiseHomeView.as_view(), name='cruises_home'),
    path('<int:pk>/', view=views.CruiseDetailView.as_view(), name='cruises_detail'),
    # AJAX paths
    path('ajax/load-navtree/', views.load_cruises_navtree, name='ajax_load_cruises_navtree'),
    path('ajax/detail/<int:pk>/', view=views.CruiseAjaxDetailView.as_view(), name='ajax_cruises_detail'),
    path('ajax/add/', view=views.CruiseAjaxCreateView.as_view(), name='ajax_cruises_add'),
    path('ajax/edit/<int:pk>/', view=views.CruiseAjaxUpdateView.as_view(), name='ajax_cruises_update'),
    path('ajax/delete/<int:pk>/', view=views.CruiseAjaxDeleteView.as_view(), name='ajax_cruises_delete'),
    path('add/', view=views.CruiseCreateView.as_view(), name='cruises_add'),
    path('edit/<int:pk>/', view=views.CruiseUpdateView.as_view(), name='cruises_update'),
    path('delete/<int:pk>/', view=views.CruiseDeleteView.as_view(), name='cruises_delete'),
    # Vessels
    path('vessels/', view=views.VesselListView.as_view(), name='vessels_home'),
    path('vessels/add/', view=views.VesselCreateView.as_view(), name='vessels_add'),
    path('vessels/edit/<int:pk>/', view=views.VesselUpdateView.as_view(), name='vessels_update'),
    path('vessels/delete/<int:pk>/', view=views.VesselDeleteView.as_view(), name='vessels_delete'),
]
