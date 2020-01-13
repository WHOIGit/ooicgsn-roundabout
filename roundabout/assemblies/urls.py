from django.urls import path

from . import views

app_name = 'assemblies'
urlpatterns = [
    path('', view=views.AssemblyHomeView.as_view(), name='assemblies_home'),
    path('<int:pk>/', view=views.AssemblyDetailView.as_view(), name='assembly_detail'),
    path('assemblypart/<int:pk>/', view=views.AssemblyPartDetailView.as_view(), name='assemblypart_detail'),
    path('assemblytype/<int:pk>/', view=views.AssemblyTypeDetailView.as_view(), name='assemblytype_detail'),
    # AJAX paths
    path('ajax/detail/<int:pk>/', view=views.AssemblyAjaxDetailView.as_view(), name='ajax_assemblies_detail'),
    path('ajax/add/', view=views.AssemblyAjaxCreateView.as_view(), name='ajax_assemblies_add'),
    path('ajax/edit/<int:pk>/', view=views.AssemblyAjaxUpdateView.as_view(), name='ajax_assemblies_update'),
    path('ajax/delete/<int:pk>/', view=views.AssemblyAjaxDeleteView.as_view(), name='ajax_assemblies_delete'),
    path('ajax/copy/<int:pk>/', view=views.AssemblyAjaxCopyView.as_view(), name='ajax_assemblies_copy'),
    path('ajax/load-navtree/', views.load_assemblies_navtree, name='ajax_load_assemblies_navtree'),
    # AssemblyPart paths
    path('ajax/assemblypart/detail/<int:pk>/', view=views.AssemblyPartAjaxDetailView.as_view(), name='ajax_assemblyparts_detail'),
    path('ajax/assemblypart/add/<int:assembly_pk>/', view=views.AssemblyPartAjaxCreateView.as_view(), name='ajax_assemblyparts_add'),
    path('ajax/assemblypart/add/<int:assembly_pk>/<int:parent_pk>/', view=views.AssemblyPartAjaxCreateView.as_view(), name='ajax_assemblyparts_add'),
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
    # API service requests
    path('api/assembly_import/', view=views.AssemblyAPIRequestCopyView.as_view(), name='assembly_api_request_import'),
]
