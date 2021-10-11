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
    path('import/csv/upload/', view=views.import_csv, name='import_csv'),
    path('import/calibrations/status/', view=views.upload_status, name='upload_status'),
    path('import/actions/comments/add/<int:pk>/', view=views.action_comment, name='action_comment_add'),
    path('import/comments/comments/add/<int:pk>/<str:crud>/', view=views.sub_comment, name='sub_comment'),
    path('import/comments/comments/delete/<int:pk>/', view=views.CommentDelete.as_view(), name='comment_comment_delete'),
    path('configure_import/update/<int:pk>/', view=views.ImportConfigUpdate.as_view(), name='import_config_edit'),
    path('bulkupload/inv_update/<int:pk>/<str:file>/<int:inv_id>', view=views.InvBulkUploadEventUpdate.as_view(), name='inv_bulkuploadevent_update'),
    path('bulkupload/part_update/<int:pk>/<str:file>/<int:part_id>', view=views.PartBulkUploadEventUpdate.as_view(), name='part_bulkuploadevent_update'),
    path('bulkupload/inv_delete/<int:pk>/<int:inv_id>', view=views.InvBulkUploadEventDelete.as_view(), name='inv_bulkuploadevent_delete'),
    path('bulkupload/part_delete/<int:pk>/<int:part_id>', view=views.PartBulkUploadEventDelete.as_view(), name='part_bulkuploadevent_delete'),

]
