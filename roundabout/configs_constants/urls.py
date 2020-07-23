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

app_name = 'configs_constants'
urlpatterns = [
    path('ajax/confname/add/<int:pk>/', view=views.PartConfNameAdd.as_view(), name='part_confname_add'),
    path('ajax/constdefault/add/<int:pk>/', view=views.EventDefaultAdd.as_view(), name='event_constdefault_add'),
    path('ajax/constdefault/edit/<int:pk>/', view=views.EventDefaultUpdate.as_view(), name='event_constdefault_update'),
    path('ajax/constdefault/delete/<int:pk>/', view=views.EventDefaultDelete.as_view(), name='event_constdefault_delete'),
    path('ajax/eventreview/delete/<int:pk>/<int:user_pk>/', view=views.event_constdefault_approve, name='event_constdefault_approve'),
    path('ajax/add/<int:pk>/', view=views.ConfigEventValueAdd.as_view(), name='config_event_value_add'),
    path('ajax/edit/<int:pk>/', view=views.ConfigEventValueUpdate.as_view(), name='config_event_value_update'),
    path('ajax/delete/<int:pk>/', view=views.ConfigEventValueDelete.as_view(), name='config_event_value_delete'),
    path('ajax/evtvaluereview/delete/<int:pk>/<int:user_pk>/', view=views.event_value_approve, name='event_value_approve'),
    path('ajax/configdefault/add/<int:pk>/', view=views.EventConfigDefaultAdd.as_view(), name='event_configdefault_add'),
    path('ajax/configdefault/edit/<int:pk>/', view=views.EventConfigDefaultUpdate.as_view(), name='event_configdefault_update'),
    path('ajax/configdefault/delete/<int:pk>/', view=views.EventConfigDefaultDelete.as_view(), name='event_configdefault_delete'),
    path('ajax/eventconfdefaultreview/delete/<int:pk>/<int:user_pk>/', view=views.event_configdefault_approve, name='event_configdefault_approve'),
]