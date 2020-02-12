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

app_name = 'deployments'
urlpatterns = [
    path('', view=views.DeploymentHomeView.as_view(), name='deployment_home'),
    path('<int:pk>/', view=views.DeploymentDetailView.as_view(), name='deployment_detail'),
    path('<int:pk>/<int:current_location>/', view=views.DeploymentDetailView.as_view(), name='deployment_detail'),
    path('deploy_confirm/<int:pk>/', view=views.DeploymentDeployConfirmView.as_view(), name='deployment_deploy_confirm'),
    path('add/', view=views.DeploymentCreateView.as_view(), name='deployment_add'),
    path('add/<int:current_location>/', view=views.DeploymentCreateView.as_view(), name='deployment_add'),
    path('edit/<int:pk>/', view=views.DeploymentUpdateView.as_view(), name='deployment_update'),
    path('edit/<int:pk>/<int:current_location>/', view=views.DeploymentUpdateView.as_view(), name='deployment_update'),
    path('delete/<int:pk>/', view=views.DeploymentDeleteView.as_view(), name='deployment_delete'),
    # AJAX paths
    path('ajax/load-navtree/', views.load_deployment_navtree, name='ajax_load_deployment_navtree'),
    path('ajax/detail/<int:pk>/', view=views.DeploymentAjaxDetailView.as_view(), name='ajax_deployment_detail'),
    path('ajax/edit/<int:pk>/', view=views.DeploymentAjaxUpdateView.as_view(), name='ajax_deployment_update'),
    path('ajax/add/', view=views.DeploymentAjaxCreateView.as_view(), name='ajax_deployment_add'),
    path('ajax/add/<int:current_location>/', view=views.DeploymentAjaxCreateView.as_view(), name='ajax_deployment_add'),
    path('ajax/action/<action_type>/<int:pk>/', view=views.DeploymentAjaxActionView.as_view(), name='ajax_deployment_action'),
    path('ajax/snapshot/<int:pk>/', view=views.DeploymentAjaxSnapshotCreateView.as_view(), name='ajax_deployment_snapshot'),
    path('ajax/snapshot/detail/<int:pk>/', view=views.DeploymentSnapshotAjaxDetailView.as_view(), name='ajax_deployment_snapshot_detail'),
    path('ajax/delete/<int:pk>/', view=views.DeploymentAjaxDeleteView.as_view(), name='ajax_deployment_delete'),
    path('ajax/snapshot/delete/<int:pk>/', view=views.DeploymentSnapshotAjaxDeleteView.as_view(), name='ajax_deployment_snapshot_delete'),
]
