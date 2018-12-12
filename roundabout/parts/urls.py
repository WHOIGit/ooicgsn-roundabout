from django.urls import path

from . import views

app_name = 'parts'
urlpatterns = [
    path('', view=views.PartsHomeView.as_view(), name='parts_home'),
    path('<int:pk>/', view=views.PartsDetailView.as_view(), name='parts_detail'),
    path('<int:pk>/<int:current_location>/', view=views.PartsDetailView.as_view(), name='parts_detail'),
    path('add/', view=views.PartsCreateView.as_view(), name='parts_add'),
    path('add/<int:pk>/<int:current_location>/', view=views.PartsSubassemblyAddView.as_view(), name='parts_subassembly_add'),
    path('edit/<int:pk>/<int:parent_pk>/<int:current_location>/', view=views.PartsSubassemblyEditView.as_view(), name='parts_subassembly_edit'),
    path('edit/<int:pk>/', view=views.PartsUpdateView.as_view(), name='parts_update'),
    path('edit/<int:pk>/<int:current_location>/', view=views.PartsUpdateView.as_view(), name='parts_update'),
    path('action/subassembly_ex/<int:pk>/<int:current_location>/', view=views.PartsSubassemblyAvailableView.as_view(), name='parts_subassembly_existing'),
    path('action/subassembly_ex/add/<int:pk>/<int:parent_pk>/<int:current_location>/', view=views.PartsSubassemblyActionView.as_view(), name='parts_subassembly_existing_add'),
    path('delete/<int:pk>/', view=views.PartsDeleteView.as_view(), name='parts_delete'),
    path('delete/<int:pk>/<int:parent_pk>/<int:current_location>/', view=views.PartsDeleteView.as_view(), name='parts_delete'),
    # AJAX paths
    path('ajax/load-navtree/', views.load_parts_navtree, name='ajax_load_parts_navtree'),
    path('ajax/detail/<int:pk>/', view=views.PartsAjaxDetailView.as_view(), name='ajax_parts_detail'),
    path('ajax/add/', view=views.PartsAjaxCreateView.as_view(), name='ajax_parts_add'),
    path('ajax/edit/<int:pk>/', view=views.PartsAjaxUpdateView.as_view(), name='ajax_parts_update'),
    path('ajax/part_type/<int:pk>/', view=views.PartsTypeAjaxDetailView.as_view(), name='ajax_parts_type_detail'),
    path('ajax/delete/<int:pk>/', view=views.PartsAjaxDeleteView.as_view(), name='ajax_parts_delete'),
    path('ajax/validate-part-number/', views.validate_part_number, name='ajax_validate_part_number'),
]
