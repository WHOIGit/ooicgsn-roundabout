from django.urls import path

from . import views

app_name = 'assemblies'
urlpatterns = [
    path('', view=views.AssemblyHomeView.as_view(), name='assemblies_home'),
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
]
