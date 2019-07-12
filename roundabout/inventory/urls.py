from django.urls import path

from . import views

app_name = 'inventory'
urlpatterns = [
    path('', view=views.InventoryHomeView.as_view(), name='inventory_home'),
    path('test/', view=views.InventoryHomeTestView.as_view(), name='inventory_home_test'),
    path('<int:pk>/', view=views.InventoryDetailView.as_view(), name='inventory_detail'),
    path('add/', view=views.InventoryCreateView.as_view(), name='inventory_add'),
    path('add/<int:current_location>/', view=views.InventoryCreateView.as_view(), name='inventory_add'),
    path('add/<int:parent_pk>/<int:current_location>/', view=views.InventoryCreateView.as_view(), name='inventory_add'),
    path('edit/<int:pk>/', view=views.InventoryUpdateView.as_view(), name='inventory_update'),
    path('edit/<int:pk>/<int:current_location>/', view=views.InventoryUpdateView.as_view(), name='inventory_update'),
    path('action/<action_type>/<int:pk>/<int:current_location>/', view=views.InventoryActionView.as_view(), name='inventory_action'),
    path('subassembly_ex/<int:pk>/<int:current_location>/', view=views.InventorySubassemblyListView.as_view(), name='inventory_subassembly_existing'),
    path('subassembly_ex/add/<int:pk>/<int:parent_pk>/<int:current_location>/', view=views.InventorySubassemblyActionView.as_view(), name='inventory_subassembly_existing_add'),
    path('delete/<int:pk>/', view=views.InventoryDeleteView.as_view(), name='inventory_delete'),
    path('search_serial/', view=views.InventorySearchSerialList.as_view(), name='inventory_search_serial'),
    path('deployment/<int:pk>/<int:current_location>/', view=views.InventoryDeploymentDetailView.as_view(), name='inventory_deployment_detail'),
    # AJAX paths
    path('ajax/load-navtree/', views.load_inventory_navtree, name='ajax_load_inventory_navtree'),
    path('ajax/detail/<int:pk>/', view=views.InventoryAjaxDetailView.as_view(), name='ajax_inventory_detail'),
    path('ajax/by-mooring-part/detail/<int:pk>/', view=views.InventoryAjaxByMooringPartDetailView.as_view(), name='ajax_inventory_mooring_part_detail'),
    path('ajax/snapshot/detail/<int:pk>/', view=views.InventoryAjaxSnapshotDetailView.as_view(), name='ajax_inventory_snapshot_detail'),
    path('ajax/edit/<int:pk>/', view=views.InventoryAjaxUpdateView.as_view(), name='ajax_inventory_update'),
    path('ajax/add/', view=views.InventoryAjaxCreateBasicView.as_view(), name='ajax_inventory_add'),
    path('ajax/add/<int:current_location>/', view=views.InventoryAjaxCreateBasicView.as_view(), name='ajax_inventory_add'),
    # Add to parent item action paths
    path('ajax/add-to-parent/<int:pk>/', view=views.InventoryAjaxParentListView.as_view(), name='ajax_inventory_add_to_parent'),
    path('ajax/add-to-parent/action/<int:pk>/<int:parent_pk>/', view=views.InventoryAjaxParentActionView.as_view(), name='ajax_inventory_add_to_parent_action'),
    # Add to build action paths
    path('ajax/add-to-build/<int:pk>/', view=views.InventoryAjaxAddToBuildListView.as_view(), name='ajax_inventory_add_to_build'),
    path('ajax/add-to-build/action/<int:pk>/<int:build_pk>/<int:assembly_part_pk>/', view=views.InventoryAjaxAddToBuildActionView.as_view(), name='ajax_inventory_add_to_build_action'),
    # Add subassembly paths
    path('ajax/add-subassembly/<int:parent_pk>/', view=views.InventoryAjaxSubassemblyListView.as_view(), name='ajax_inventory_add_subassembly'),
    path('ajax/add-subassembly/action/<int:pk>/<int:parent_pk>/', view=views.InventoryAjaxSubassemblyActionView.as_view(), name='ajax_inventory_add_subassembly_action'),
    # Add subassembly by Mooring Part
    path('ajax/add-subassembly/mooring-part/<int:pk>/<int:location_pk>/<int:deployment_pk>/', view=views.InventoryByMooringPartAjaxSubassemblyListView.as_view(), name='ajax_inventory_mooring_part_add_subassembly'),
    path('ajax/add-subassembly/mooring-part/action/<int:pk>/<int:deployment_pk>/<int:mooring_part_pk>/', view=views.InventoryByMooringPartAjaxSubassemblyActionView.as_view(), name='ajax_inventory_mooring_part_add_subassembly_action'),
    path('ajax/add-subassembly/mooring-part/action/<int:pk>/<int:deployment_pk>/<int:mooring_part_pk>/<int:parent_pk>/', view=views.InventoryByMooringPartAjaxSubassemblyActionView.as_view(), name='ajax_inventory_mooring_part_add_subassembly_action'),
    # Add subassembly by Assembly Part
    path('ajax/add-subassembly/assembly-part/<int:pk>/<int:location_pk>/<int:build_pk>/', view=views.InventoryAjaxByAssemblyPartListView.as_view(), name='ajax_inventory_assembly_part_add_subassembly'),
    path('ajax/add-subassembly/assembly-part/action/<int:pk>/<int:build_pk>/<int:assembly_part_pk>/', view=views.InventoryAjaxByAssemblyPartyActionView.as_view(), name='ajax_inventory_assembly_part_add_subassembly_action'),
    path('ajax/add-subassembly/assembly-part/action/<int:pk>/<int:build_pk>/<int:assembly_part_pk>/<int:parent_pk>/', view=views.InventoryAjaxByAssemblyPartyActionView.as_view(), name='ajax_inventory_assembly_part_add_subassembly_action'),
    # Assign Destination paths
    path('ajax/assign-destination/<int:pk>/', view=views.InventoryAjaxAssignDestinationView.as_view(), name='ajax_inventory_assign_destination'),
    path('ajax/assign-destination/action/<int:pk>/<int:mooring_part_pk>/', view=views.InventoryAjaxAssignDestinationActionView.as_view(), name='ajax_inventory_assign_destination_action'),
    path('ajax/destination/<int:pk>/<int:location_pk>/<int:assigned_destination_root_pk>/', view=views.InventoryAjaxDestinationSubassemblyListView.as_view(), name='ajax_inventory_destination_add_subassembly'),
    path('ajax/destination/action/<int:pk>/<int:mooring_part_pk>/<int:location_pk>/<int:assigned_destination_root_pk>/', view=views.InventoryAjaxDestinationSubassemblyActionView.as_view(), name='ajax_inventory_destination_add_subassembly_action'),
    path('ajax/destination/action/<int:pk>/<int:mooring_part_pk>/<int:location_pk>/<int:assigned_destination_root_pk>/<int:parent_pk>/', view=views.InventoryAjaxDestinationSubassemblyActionView.as_view(), name='ajax_inventory_destination_add_subassembly_action'),
    path('ajax/edit/<int:pk>/', view=views.InventoryAjaxUpdateView.as_view(), name='ajax_inventory_update'),
    path('ajax/action/<action_type>/<int:pk>/', view=views.InventoryAjaxActionView.as_view(), name='ajax_inventory_action'),
    path('ajax/note/<int:pk>/', view=views.ActionNoteAjaxCreateView.as_view(), name='ajax_note_action'),
    path('ajax/photo-upload/<int:pk>/', view=views.ActionPhotoUploadAjaxCreateView.as_view(), name='ajax_photo_upload_action'),
    path('ajax/history/<int:pk>/', view=views.ActionHistoryNoteAjaxCreateView.as_view(), name='ajax_history_action'),
    path('ajax/location/<int:pk>/', view=views.InventoryAjaxLocationDetailView.as_view(), name='ajax_inventory_location_detail'),
    path('ajax/delete/<int:pk>/', view=views.InventoryAjaxDeleteView.as_view(), name='ajax_inventory_delete'),
    path('ajax/load-part-templates/', views.load_part_templates, name='ajax_load_part_templates'),
    path('ajax/load-part-templates-by-partnumber/', views.load_part_templates_by_partnumber, name='ajax_load_part_templates_by_partnumber'),
    path('ajax/load-revisions-by-partnumber/', views.load_revisions_by_partnumber, name='ajax_load_revisions_by_partnumber'),
    path('ajax/load-part-number-for-serialnumber/', views.load_partnumber_create_serialnumber, name='ajax_load_partnumber_create_serialnumber'),
    path('ajax/load-part-templates-for-serialnumber/', views.load_parttemplate_create_serialnumber, name='ajax_load_parttemplate_create_serialnumber'),
    path('ajax/load-subassemblies-by-serialnumber/', views.load_subassemblies_by_serialnumber, name='ajax_load_subassemblies_by_serialnumber'),
    path('ajax/load-mooringpart-subassemblies-by-serialnumber/', views.load_mooringpart_subassemblies_by_serialnumber, name='ajax_load_mooringpart_subassemblies_by_serialnumber'),
    path('ajax/load-destination-subassemblies-by-serialnumber/', views.load_destination_subassemblies_by_serialnumber, name='ajax_load_destination_subassemblies_by_serialnumber'),
    path('ajax/load-parents/', views.load_parents, name='ajax_load_parents'),
    path('ajax/load-deployments/', views.load_deployments, name='ajax_load_deployments'),
    path('ajax/load-mooring-parts/', views.load_mooring_parts, name='ajax_load_mooring_parts'),
    path('ajax/load-is-equipment/', views.load_is_equipment, name='ajax_load_is_equipment'),
    path('ajax/filter-navtree/', views.filter_inventory_navtree, name='ajax_filter_inventory_navtree'),
    path('ajax/print-code/<code_format>/', views.print_code_zebraprinter, name='ajax_print_code'),
]
