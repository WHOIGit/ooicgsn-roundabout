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

app_name = 'export'
urlpatterns = [
    path('',view=views.HomeView.as_view(),name='dash'),
    path('calibration_event/<int:pk>/', view=views.ExportCalibrationEvent.as_view(), name='calibration'),
    path('calibration_events/', view=views.ExportCalibrationEvents.as_view(), name='calibrations'),
    path('configurations/', view=views.ExportConfigConst.as_view(), name='configurations'),
    path('cruises/', view=views.ExportCruises.as_view(), name='cruises'),
    path('vessels/', view=views.ExportVessels.as_view(), name='vessels'),
    path('deployments/', view=views.ExportDeployments.as_view(), name='deployments'),
]
