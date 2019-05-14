from django.urls import path

from . import views

app_name = 'userdefinedfields'
urlpatterns = [
    path('', view=views.UserDefinedFieldListView.as_view(), name='fields_home'),
    path('add/', view=views.UserDefinedFieldCreateView.as_view(), name='fields_add'),
]
