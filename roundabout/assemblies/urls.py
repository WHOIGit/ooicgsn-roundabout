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

app_name = 'assemblies'
urlpatterns = [
    path('', view=views.AssemblyHomeView.as_view(), name='assemblies_home'),
    path('<int:pk>/', view=views.AssemblyDetailView.as_view(), name='assembly_detail'),
    path('assemblypart/<int:pk>/', view=views.AssemblyPartDetailView.as_view(), name='assemblypart_detail'),
    path('assemblyrevision/<int:pk>/', view=views.AssemblyRevisionDetailView.as_view(), name='assemblyrevision_detail'),
    path('assemblytype/<int:pk>/', view=views.AssemblyTypeDetailView.as_view(), name='assemblytype_detail'),
    # AJAX paths
    path('ajax/detail/<int:pk>/', view=views.AssemblyAjaxDetailView.as_view(), name='ajax_assemblies_detail'),
    path('ajax/add/', view=views.AssemblyAjaxCreateView.as_view(), name='ajax_assemblies_add'),
    path('ajax/edit/<int:pk>/', view=views.AssemblyAjaxUpdateView.as_view(), name='ajax_assemblies_update'),
    path('ajax/delete/<int:pk>/', view=views.AssemblyAjaxDeleteView.as_view(), name='ajax_assemblies_delete'),
    path('ajax/copy/<int:assembly_to_copy_pk>/', view=views.AssemblyAjaxCopyView.as_view(), name='ajax_assemblies_copy'),
    path('ajax/load-navtree/', views.load_assemblies_navtree, name='ajax_load_assemblies_navtree'),
    # Revision paths
    path('ajax/revision/detail/<int:pk>/', view=views.AssemblyRevisionAjaxDetailView.as_view(), name='ajax_assemblyrevision_detail'),
    path('ajax/revision/create/<int:assembly_pk>/', view=views.AssemblyRevisionAjaxCreateView.as_view(), name='ajax_assemblies_create_revision'),
    path('ajax/revision/create/<int:assembly_pk>/<int:assembly_revision_pk>/', view=views.AssemblyRevisionAjaxCreateView.as_view(), name='ajax_assemblies_create_revision'),
    path('ajax/revision/edit/<int:pk>/', view=views.AssemblyRevisionAjaxUpdateView.as_view(), name='ajax_assemblies_update_revision'),
    path('ajax/revision/delete/<int:pk>/', view=views.AssemblyRevisionAjaxDeleteView.as_view(), name='ajax_assemblies_delete_revision'),
    # AssemblyPart paths
    path('ajax/assemblypart/detail/<int:pk>/', view=views.AssemblyPartAjaxDetailView.as_view(), name='ajax_assemblyparts_detail'),
    path('ajax/assemblypart/add/<int:assembly_revision_pk>/', view=views.AssemblyPartAjaxCreateView.as_view(), name='ajax_assemblyparts_add'),
    path('ajax/assemblypart/add/<int:assembly_revision_pk>/<int:parent_pk>/', view=views.AssemblyPartAjaxCreateView.as_view(), name='ajax_assemblyparts_add'),
    path('ajax/assemblypart/edit/<int:pk>/', view=views.AssemblyPartAjaxUpdateView.as_view(), name='ajax_assemblyparts_update'),
    path('ajax/assemblypart/delete/<int:pk>/', view=views.AssemblyPartAjaxDeleteView.as_view(), name='ajax_assemblyparts_delete'),
    path('ajax/load-part-templates/', views.load_part_templates, name='ajax_load_part_templates'),
    path('ajax/load-assembly-parts/', views.load_assembly_parts, name='ajax_load_assembly_parts'),
    # AssemblyType paths
    path('ajax/assemblytype/detail/<int:pk>/', view=views.AssemblyTypeAjaxDetailView.as_view(), name='ajax_assembly_type_detail'),
    path('assemblytype/', view=views.AssemblyTypeListView.as_view(), name='assembly_type_home'),
    path('assemblytype/add/', view=views.AssemblyTypeCreateView.as_view(), name='assembly_type_add'),
    path('assemblytype/edit/<int:pk>/', view=views.AssemblyTypeUpdateView.as_view(), name='assembly_type_update'),
    path('assemblytype/delete/<int:pk>/', view=views.AssemblyTypeDeleteView.as_view(), name='assembly_type_delete'),
    path('ajax/referencedesignator/edit/<int:pk>/', view=views.EventReferenceDesignatorUpdate.as_view(), name='event_referencedesignator_update'),
    path('ajax/referencedesignator/create/<int:pk>/', view=views.EventReferenceDesignatorAdd.as_view(), name='event_referencedesignator_add'),
    path('ajax/referencedesignator/delete/<int:pk>/', view=views.EventReferenceDesignatorDelete.as_view(), name='event_referencedesignator_delete'),
]
