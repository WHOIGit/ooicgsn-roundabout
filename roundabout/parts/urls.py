from django.urls import path

from . import views

app_name = 'parts'
urlpatterns = [
    path('', view=views.PartsHomeView.as_view(), name='parts_home'),
    path('<int:pk>/', view=views.PartsDetailView.as_view(), name='parts_detail'),
    path('add/', view=views.PartsCreateView.as_view(), name='parts_add'),
    path('edit/<int:pk>/', view=views.PartsUpdateView.as_view(), name='parts_update'),
    path('edit/<int:pk>/<int:current_location>/', view=views.PartsUpdateView.as_view(), name='parts_update'),
    path('delete/<int:pk>/', view=views.PartsDeleteView.as_view(), name='parts_delete'),
    path('delete/<int:pk>/<int:parent_pk>/<int:current_location>/', view=views.PartsDeleteView.as_view(), name='parts_delete'),
    # AJAX paths
    path('ajax/load-navtree/', views.load_parts_navtree, name='ajax_load_parts_navtree'),
    path('ajax/detail/<int:pk>/', view=views.PartsAjaxDetailView.as_view(), name='ajax_parts_detail'),
    path('ajax/add/', view=views.PartsAjaxCreateView.as_view(), name='ajax_parts_add'),
    path('ajax/edit/<int:pk>/', view=views.PartsAjaxUpdateView.as_view(), name='ajax_parts_update'),
    path('ajax/revision/create/<int:part_pk>/', view=views.PartsAjaxCreateRevisionView.as_view(), name='ajax_parts_create_revision'),
    path('ajax/revision/edit/<int:pk>/', view=views.PartsAjaxUpdateRevisionView.as_view(), name='ajax_parts_update_revision'),
    path('ajax/revision/delete/<int:pk>/', view=views.PartsAjaxDeleteRevisionView.as_view(), name='ajax_parts_delete_revision'),
    path('ajax/part_type/<int:pk>/', view=views.PartsTypeAjaxDetailView.as_view(), name='ajax_parts_type_detail'),
    path('ajax/userdefinedfields/add/<int:pk>/', view=views.PartsAjaxAddUdfFieldUpdateView.as_view(), name='ajax_parts_add_udf_field'),
    path('ajax/userdefinedfields/setvalue/<int:pk>/<int:field_pk>/', view=views.PartsAjaxSetUdfFieldValueFormView.as_view(), name='ajax_parts_set_udf_fieldvalue'),
    path('ajax/userdefinedfields/remove/<int:pk>/<int:field_pk>/', view=views.PartsAjaxRemoveUdfFieldView.as_view(), name='ajax_parts_remove_udf_field'),
    path('ajax/userdefinedfields/remove/action/<int:pk>/<int:field_pk>/', view=views.PartsAjaxRemoveActionUdfFieldView.as_view(), name='ajax_parts_remove_action_udf_field'),
    path('ajax/delete/<int:pk>/', view=views.PartsAjaxDeleteView.as_view(), name='ajax_parts_delete'),
    path('ajax/validate-part-number/', views.validate_part_number, name='ajax_validate_part_number'),
    # PartType paths
    path('part_type/<int:pk>/', view=views.PartsTypeDetailView.as_view(), name='parts_type_detail'),
    path('part_type/', view=views.PartsTypeListView.as_view(), name='parts_type_home'),
    path('part_type/add/', view=views.PartsTypeCreateView.as_view(), name='parts_type_add'),
    path('part_type/edit/<int:pk>/', view=views.PartsTypeUpdateView.as_view(), name='parts_type_update'),
    path('part_type/delete/<int:pk>/', view=views.PartsTypeDeleteView.as_view(), name='parts_type_delete'),
]
