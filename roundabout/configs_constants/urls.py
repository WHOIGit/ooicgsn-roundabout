from django.urls import path

from . import views

app_name = 'configs_constants'
urlpatterns = [
    path('ajax/confname/add/<int:pk>/', view=views.PartConfNameAdd.as_view(), name='part_confname_add'),
    path('ajax/add/<int:pk>/', view=views.ConfigEventValueAdd.as_view(), name='config_event_value_add'),
    path('ajax/edit/<int:pk>/', view=views.ConfigEventValueUpdate.as_view(), name='config_event_value_update'),
    path('ajax/delete/<int:pk>/', view=views.ConfigEventValueDelete.as_view(), name='config_event_value_delete'),
]