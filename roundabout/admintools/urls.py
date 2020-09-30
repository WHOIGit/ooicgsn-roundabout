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

app_name = 'admintools'
urlpatterns = [
    path('sentry-debug/', views.trigger_error),
    #Import Deployments
    path('import/deployments/upload/', view=views.ImportDeploymentsUploadView.as_view(), name='import_deployments_upload'),
    #Import Calibrations
    path('import/calibrations/upload/', view=views.ImportCalibrationsUploadView.as_view(), name='import_calibrations_upload'),
    # Printers
    path('printers/', view=views.PrinterListView.as_view(), name='printers_home'),
    path('printers/add/', view=views.PrinterCreateView.as_view(), name='printers_add'),
    path('printers/edit/<int:pk>/', view=views.PrinterUpdateView.as_view(), name='printers_update'),
    path('printers/delete/<int:pk>/', view=views.PrinterDeleteView.as_view(), name='printers_delete'),
    # Import tool
    path('import/inventory/create-template/', view=views.ImportInventoryCreateTemplateView.as_view(), name='import_inventory_create_template'),
    path('import/inventory/upload/', view=views.ImportInventoryUploadView.as_view(), name='import_inventory_upload'),
    path('import/inventory/upload/<int:pk>/', view=views.ImportInventoryPreviewDetailView.as_view(), name='import_inventory_preview_detail'),
    path('import/inventory/upload/add/<int:pk>/', view=views.ImportInventoryUploadAddActionView.as_view(), name='import_inventory_upload_add_action'),
    path('import/inventory/upload/success/', view=views.ImportInventoryUploadSuccessView.as_view(), name='import_inventory_upload_success'),
    # API service requests
    path('import/assembly/api-request/', view=views.ImportAssemblyAPIRequestCopyView.as_view(), name='import_assembly_api_request'),
]
