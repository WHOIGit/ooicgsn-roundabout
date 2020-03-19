from django.urls import path

from . import views

app_name = 'calibrations'
urlpatterns = [
    path('ajax/add/<int:pk>/', view=views.CalibrationsAddView.as_view(), name='calibrations_form')
]