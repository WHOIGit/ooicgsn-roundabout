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

from . import views, views_tests

app_name = "inventory"
urlpatterns = [
    path("", view=views.InventoryHomeView.as_view(), name="inventory_home"),
    path(
        "<int:pk>/", view=views.InventoryDetailView.as_view(), name="inventory_detail"
    ),
    # AJAX paths
    path(
        "ajax/load-navtree/",
        views.load_inventory_navtree,
        name="ajax_load_inventory_navtree",
    ),
    path(
        "ajax/detail/<int:pk>/",
        view=views.InventoryAjaxDetailView.as_view(),
        name="ajax_inventory_detail",
    ),
    path(
        "ajax/snapshot/detail/<int:pk>/",
        view=views.InventoryAjaxSnapshotDetailView.as_view(),
        name="ajax_inventory_snapshot_detail",
    ),
    path(
        "ajax/edit/<int:pk>/",
        view=views.InventoryAjaxUpdateView.as_view(),
        name="ajax_inventory_update",
    ),
    path(
        "ajax/add/",
        view=views.InventoryAjaxCreateBasicView.as_view(),
        name="ajax_inventory_add",
    ),
    path(
        "ajax/add/<int:current_location>/",
        view=views.InventoryAjaxCreateBasicView.as_view(),
        name="ajax_inventory_add",
    ),
    # Add to parent item action paths
    path(
        "ajax/add-to-parent/<int:pk>/",
        view=views.InventoryAjaxParentListView.as_view(),
        name="ajax_inventory_add_to_parent",
    ),
    path(
        "ajax/add-to-parent/action/<int:pk>/<int:parent_pk>/",
        view=views.InventoryAjaxParentActionView.as_view(),
        name="ajax_inventory_add_to_parent_action",
    ),
    # Add to build action paths
    path(
        "ajax/add-to-build/<int:pk>/",
        view=views.InventoryAjaxAddToBuildListView.as_view(),
        name="ajax_inventory_add_to_build",
    ),
    path(
        "ajax/add-to-build/action/<int:pk>/<int:build_pk>/<int:assembly_part_pk>/",
        view=views.InventoryAjaxAddToBuildActionView.as_view(),
        name="ajax_inventory_add_to_build_action",
    ),
    # Add subassembly paths
    path(
        "ajax/add-subassembly/<int:parent_pk>/",
        view=views.InventoryAjaxSubassemblyListView.as_view(),
        name="ajax_inventory_add_subassembly",
    ),
    path(
        "ajax/add-subassembly/action/<int:pk>/<int:parent_pk>/",
        view=views.InventoryAjaxSubassemblyActionView.as_view(),
        name="ajax_inventory_add_subassembly_action",
    ),
    # Add subassembly by Assembly Part
    path(
        "ajax/add-subassembly/assembly-part/<int:pk>/<int:location_pk>/<int:build_pk>/",
        view=views.InventoryAjaxByAssemblyPartListView.as_view(),
        name="ajax_inventory_assembly_part_add_subassembly",
    ),
    path(
        "ajax/add-subassembly/assembly-part/action/<int:pk>/<int:build_pk>/<int:assembly_part_pk>/",
        view=views.InventoryAjaxByAssemblyPartActionView.as_view(),
        name="ajax_inventory_assembly_part_add_subassembly_action",
    ),
    path(
        "ajax/add-subassembly/assembly-part/action/<int:pk>/<int:build_pk>/<int:assembly_part_pk>/<int:parent_pk>/",
        view=views.InventoryAjaxByAssemblyPartActionView.as_view(),
        name="ajax_inventory_assembly_part_add_subassembly_action",
    ),
    # Assign Destination paths
    path(
        "ajax/assign-destination/<int:pk>/",
        view=views.InventoryAjaxAssignDestinationView.as_view(),
        name="ajax_inventory_assign_destination",
    ),
    path(
        "ajax/assign-destination/action/<int:pk>/<int:assembly_part_pk>/",
        view=views.InventoryAjaxAssignDestinationActionView.as_view(),
        name="ajax_inventory_assign_destination_action",
    ),
    path(
        "ajax/destination/<int:pk>/<int:location_pk>/<int:assigned_destination_root_pk>/",
        view=views.InventoryAjaxDestinationSubassemblyListView.as_view(),
        name="ajax_inventory_destination_add_subassembly",
    ),
    path(
        "ajax/destination/action/<int:pk>/<int:assembly_part_pk>/<int:location_pk>/<int:assigned_destination_root_pk>/",
        view=views.InventoryAjaxDestinationSubassemblyActionView.as_view(),
        name="ajax_inventory_destination_add_subassembly_action",
    ),
    path(
        "ajax/destination/action/<int:pk>/<int:assembly_part_pk>/<int:location_pk>/<int:assigned_destination_root_pk>/<int:parent_pk>/",
        view=views.InventoryAjaxDestinationSubassemblyActionView.as_view(),
        name="ajax_inventory_destination_add_subassembly_action",
    ),
    # Base action paths
    path(
        "ajax/edit/<int:pk>/",
        view=views.InventoryAjaxUpdateView.as_view(),
        name="ajax_inventory_update",
    ),
    path(
        "ajax/action/<action_type>/<int:pk>/",
        view=views.InventoryAjaxActionView.as_view(),
        name="ajax_inventory_action",
    ),
    path(
        "ajax/note/<int:pk>/",
        view=views.ActionNoteAjaxCreateView.as_view(),
        name="ajax_note_action",
    ),
    path(
        "ajax/deploy/<int:pk>/",
        view=views.ActionDeployInventoryAjaxFormView.as_view(),
        name="ajax_deploy_action",
    ),
    path(
        "ajax/photo-upload/<int:pk>/",
        view=views.ActionPhotoUploadAjaxCreateView.as_view(),
        name="ajax_photo_upload_action",
    ),
    path(
        "ajax/history/<int:pk>/",
        view=views.ActionHistoryNoteAjaxCreateView.as_view(),
        name="ajax_history_action",
    ),
    path(
        "ajax/location/<int:pk>/",
        view=views.InventoryAjaxLocationDetailView.as_view(),
        name="ajax_inventory_location_detail",
    ),
    path(
        "ajax/delete/<int:pk>/",
        view=views.InventoryAjaxDeleteView.as_view(),
        name="ajax_inventory_delete",
    ),
    # Inventory Deployment paths
    path(
        "ajax/inventory-deployment/edit/<int:pk>/",
        view=views.InventoryDeploymentAjaxUpdateView.as_view(),
        name="ajax_inventory_deployment_update",
    ),
    path(
        "ajax/snapshot/<int:pk>/",
        view=views.DeploymentAjaxSnapshotCreateView.as_view(),
        name="ajax_deployment_snapshot",
    ),
    path(
        "ajax/snapshot/detail/<int:pk>/",
        view=views.DeploymentSnapshotAjaxDetailView.as_view(),
        name="ajax_deployment_snapshot_detail",
    ),
    path(
        "ajax/snapshot/delete/<int:pk>/",
        view=views.DeploymentSnapshotAjaxDeleteView.as_view(),
        name="ajax_deployment_snapshot_delete",
    ),
    # Javascript AJAX filter paths
    path(
        "ajax/load-part-templates/",
        views.load_part_templates,
        name="ajax_load_part_templates",
    ),
    path(
        "ajax/load-part-templates-by-partnumber/",
        views.load_part_templates_by_partnumber,
        name="ajax_load_part_templates_by_partnumber",
    ),
    path(
        "ajax/load-revisions-by-partnumber/",
        views.load_revisions_by_partnumber,
        name="ajax_load_revisions_by_partnumber",
    ),
    path(
        "ajax/load-new-serialnumber/",
        views.load_new_serialnumber,
        name="ajax_load_new_serialnumber",
    ),
    path(
        "ajax/load-subassemblies-by-serialnumber/",
        views.load_subassemblies_by_serialnumber,
        name="ajax_load_subassemblies_by_serialnumber",
    ),
    path(
        "ajax/load-destination-subassemblies-by-serialnumber/",
        views.load_destination_subassemblies_by_serialnumber,
        name="ajax_load_destination_subassemblies_by_serialnumber",
    ),
    path(
        "ajax/load-build-subassemblies-by-serialnumber/",
        views.load_build_subassemblies_by_serialnumber,
        name="ajax_load_build_subassemblies_by_serialnumber",
    ),
    path("ajax/load-parents/", views.load_parents, name="ajax_load_parents"),
    path(
        "ajax/load-deployments/", views.load_deployments, name="ajax_load_deployments"
    ),
    path(
        "ajax/print-code/<int:pk>/<code_format>/",
        views.print_code_zebraprinter,
        name="ajax_print_code",
    ),
    # Test paths
    path(
        "test/<int:pk>/",
        view=views_tests.InventoryTestDetailView.as_view(),
        name="test_detail",
    ),
    path("test/", view=views_tests.InventoryTestListView.as_view(), name="test_home"),
    path(
        "test/add/", view=views_tests.InventoryTestCreateView.as_view(), name="test_add"
    ),
    path(
        "test/edit/<int:pk>/",
        view=views_tests.InventoryTestUpdateView.as_view(),
        name="test_update",
    ),
    path(
        "test/delete/<int:pk>/",
        view=views_tests.InventoryTestDeleteView.as_view(),
        name="test_delete",
    ),
    path(
        "ajax/test-result/<int:inventory_pk>/",
        views_tests.InventoryTestResultAjaxCreateView.as_view(),
        name="ajax_test_result",
    ),
    path(
        "ajax/test-result/<int:inventory_pk>/<int:test_pk>/",
        views_tests.InventoryTestResultAjaxCreateView.as_view(),
        name="ajax_test_result",
    ),
    path(
        "test/reset-all-tests/<int:inventory_pk>/",
        view=views_tests.InventoryTestResetAllActionView.as_view(),
        name="ajax_test_reset_all_tests",
    ),
]
