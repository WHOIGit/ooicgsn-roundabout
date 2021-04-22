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

app_name = 'calibrations'
urlpatterns = [
    path('ajax/add/<int:pk>/', view=views.EventValueSetAdd.as_view(), name='event_valueset_add'),
    path('ajax/edit/<int:pk>/', view=views.EventValueSetUpdate.as_view(), name='event_valueset_update'),
    path('ajax/delete/<int:pk>/', view=views.EventValueSetDelete.as_view(), name='event_valueset_delete'),
    path('ajax/value/edit/<int:pk>/<str:sel_ids>/', view=views.ValueSetValueUpdate.as_view(), name='valueset_value_update'),
    path('ajax/calname/add/<int:pk>/', view=views.EventCoeffNameAdd.as_view(), name='event_coeffname_add'),
    path('ajax/calname/edit/<int:pk>/', view=views.EventCoeffNameUpdate.as_view(), name='event_coeffname_update'),
    path('ajax/calname/delete/<int:pk>/', view=views.EventCoeffNameDelete.as_view(), name='event_coeffname_delete'),
    path('ajax/eventreview/delete/<int:pk>/<int:user_pk>/<str:evt_type>/', view=views.event_review_toggle, name='event_review_toggle'),
]
