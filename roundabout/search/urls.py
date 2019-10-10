from django.urls import path

from . import views

app_name = 'search'
urlpatterns = [
    path('', view=views.BasicSearch.as_view(), name='basic'),
]
