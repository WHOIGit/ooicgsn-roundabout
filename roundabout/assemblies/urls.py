from django.urls import path

from . import views

app_name = 'assemblies'
urlpatterns = [
    path('', view=views.AssemblyHomeView.as_view(), name='assemblies_home'),
    # AJAX paths
    path('ajax/load-navtree/', views.load_assemblies_navtree, name='ajax_load_assemblies_navtree'),
]
