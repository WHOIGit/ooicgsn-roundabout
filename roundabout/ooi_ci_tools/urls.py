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

app_name = 'ooi_ci_tools'
urlpatterns = [
    #Import Deployments
    path('import/deployments/upload/', view=views.ImportDeploymentsUploadView.as_view(), name='import_deployments_upload'),
    #Import Vessels
    path('import/vessels/upload/', view=views.ImportVesselsUploadView.as_view(), name='import_vessels_upload'),
    #Import Vessels
    path('import/cruises/upload/', view=views.ImportCruisesUploadView.as_view(), name='import_cruises_upload'),
    #Import Calibrations
    #path('import/calibrations/upload/', view=views.ImportCalibrationsUploadView.as_view(), name='import_calibrations_upload'),
    path('import/upload/success/', view=views.ImportUploadSuccessView.as_view(), name='import_upload_success'),
    #Import Calibrations
    path('import/csv/upload/', view=views.import_csv, name='import_csv'),
    path('import/calibrations/status/', view=views.upload_status, name='upload_status'),
    path('import/actions/comments/add/<int:pk>/', view=views.ActionCommentAdd.as_view(), name='action_comment_add'),
]
