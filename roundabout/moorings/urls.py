from django.urls import path

from . import views

app_name = 'moorings'
urlpatterns = [
    path('', view=views.MooringsHomeView.as_view(), name='moorings_home'),
    path('test/', view=views.MooringsHomeTestView.as_view(), name='moorings_home_test'),
    path('<int:pk>/', view=views.MooringsDetailView.as_view(), name='moorings_detail'),
    path('<int:pk>/<int:current_location>/', view=views.MooringsDetailView.as_view(), name='moorings_detail'),
    path('add/', view=views.MooringsCreateView.as_view(), name='moorings_add'),
    path('add/<int:current_location>/', view=views.MooringsCreateView.as_view(), name='moorings_add'),
    path('add/<int:parent_pk>/<int:current_location>/', view=views.MooringsCreateView.as_view(), name='moorings_add'),
    path('subassembly/add/<int:parent_pk>/<int:current_location>/', view=views.MooringsSubassemblyAddView.as_view(), name='moorings_subassembly_add'),
    path('edit/<int:pk>/', view=views.MooringsUpdateView.as_view(), name='moorings_update'),
    path('delete/<int:pk>/', view=views.MooringsDeleteView.as_view(), name='moorings_delete'),
    # AJAX paths
    path('ajax/load-navtree/', views.load_moorings_navtree, name='ajax_load_moorings_navtree'),
    path('ajax/detail/<int:pk>/', view=views.MooringsAjaxDetailView.as_view(), name='ajax_moorings_detail'),
    path('ajax/add/', view=views.MooringsAjaxCreateView.as_view(), name='ajax_moorings_add'),
    path('ajax/add/<int:parent_pk>/<int:current_location>/', view=views.MooringsAjaxCreateView.as_view(), name='ajax_moorings_add'),
    path('ajax/edit/<int:pk>/', view=views.MooringsAjaxUpdateView.as_view(), name='ajax_moorings_update'),
    path('ajax/delete/<int:pk>/', view=views.MooringsAjaxDeleteView.as_view(), name='ajax_moorings_delete'),
    path('ajax/copy/<int:pk>/', view=views.MooringsCopyAssemblyView.as_view(), name='ajax_moorings_copy'),
    path('ajax/copy/location/<int:pk>/', view=views.MooringsCopyLocationView.as_view(), name='ajax_moorings_location_copy'),
    path('ajax/detail/location/<int:pk>/', view=views.MooringsAjaxLocationDetailView.as_view(), name='ajax_moorings_location_detail'),
    path('ajax/load-part-templates/', views.load_part_templates, name='ajax_load_part_templates'),
    path('ajax/load-mooring-parts/', views.load_mooring_parts, name='ajax_load_mooring_parts'),
    path('ajax/filter-navtree/', views.filter_moorings_navtree, name='ajax_filter_moorings_navtree'),
]
