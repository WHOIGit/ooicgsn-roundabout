from django.urls import path

from . import views

app_name = 'calibrations'
urlpatterns = [
    path('ajax/add/<int:pk>/', view=views.EventValueSetAdd.as_view(), name='event_valueset_add'),
    path('ajax/edit/<int:pk>/', view=views.EventValueSetUpdate.as_view(), name='event_valueset_update'),
    path('ajax/delete/<int:pk>/', view=views.EventValueSetDelete.as_view(), name='event_valueset_delete')
]