from django.urls import path

from . import views

app_name = 'userdefinedfields'
urlpatterns = [
    path('', view=views.UserDefinedFieldListView.as_view(), name='fields_home'),
    path('add/', view=views.UserDefinedFieldCreateView.as_view(), name='fields_add'),
    path('edit/<int:pk>/', view=views.UserDefinedFieldUpdateView.as_view(), name='fields_update'),
    path('delete/<int:pk>/', view=views.UserDefinedFieldDeleteView.as_view(), name='fields_delete'),
]
