from django.urls import path

from . import views

app_name = 'configs_constants'
urlpatterns = [
    path('ajax/confname/add/<int:pk>/', view=views.PartConfNameAdd.as_view(), name='part_confname_add'),
    path('ajax/constdefault/add/<int:pk>/', view=views.EventDefaultAdd.as_view(), name='event_constdefault_add'),
    path('ajax/constdefault/edit/<int:pk>/', view=views.EventDefaultUpdate.as_view(), name='event_constdefault_update'),
    path('ajax/constdefault/delete/<int:pk>/', view=views.EventDefaultDelete.as_view(), name='event_constdefault_delete'),
    path('ajax/eventreview/delete/<int:pk>/<int:user_pk>/', view=views.event_constdefault_approve, name='event_constdefault_approve'),
    path('ajax/add/<int:pk>/', view=views.ConfigEventValueAdd.as_view(), name='config_event_value_add'),
    path('ajax/edit/<int:pk>/', view=views.ConfigEventValueUpdate.as_view(), name='config_event_value_update'),
    path('ajax/delete/<int:pk>/', view=views.ConfigEventValueDelete.as_view(), name='config_event_value_delete'),
    path('ajax/evtvaluereview/delete/<int:pk>/<int:user_pk>/', view=views.event_value_approve, name='event_value_approve'),
]