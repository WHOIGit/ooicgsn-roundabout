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

app_name = 'exports'
urlpatterns = [
    path('',view=views.HomeView.as_view(),name='home'),
    path('calibration_event/<int:pk>/', view=views.ExportCalibrationEvent.as_view(), name='calibration'),
    path('configconst_event/<int:pk>', view=views.ExportConfigEvent.as_view(), name='configconst'),
    path('calibration_events/', view=views.ExportCalibrationEvents.as_view(), name='calibrations'),
    path('configconst_events/', view=views.ExportConfigEvents.as_view(), name='configconsts'),
    path('cruises/', view=views.ExportCruises.as_view(), name='cruises'),
    path('vessels/', view=views.ExportVessels.as_view(), name='vessels'),
    path('deployments/', view=views.ExportDeployments.as_view(), name='deployments'),
]
