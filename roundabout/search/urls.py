from django.urls import path

from . import views

app_name = 'reports'
urlpatterns = [
    path('', view=views.BasicSearch.as_view(), name='main'),
]
