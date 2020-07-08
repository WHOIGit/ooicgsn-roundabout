from django.urls import path

from . import views

app_name = 'calibrations'
urlpatterns = [
    path('ajax/add/<int:pk>/', view=views.EventValueSetAdd.as_view(), name='event_valueset_add'),
    path('ajax/edit/<int:pk>/', view=views.EventValueSetUpdate.as_view(), name='event_valueset_update'),
    path('ajax/delete/<int:pk>/', view=views.EventValueSetDelete.as_view(), name='event_valueset_delete'),
    path('ajax/value/edit/<int:pk>/', view=views.ValueSetValueUpdate.as_view(), name='valueset_value_update'),
    path('ajax/calname/add/<int:pk>/', view=views.PartCalNameAdd.as_view(), name='part_calname_add'),
    path('ajax/eventreview/delete/<int:pk>/<int:user_pk>/', view=views.event_review_approve, name='event_review_delete'),
    path('export/<int:pk>/', view=views.ExportCalibrationEvent.as_view(), name='export_calibration'),
]
