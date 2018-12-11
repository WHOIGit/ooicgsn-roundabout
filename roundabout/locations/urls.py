from django.urls import path

from . import views

app_name = 'locations'
urlpatterns = [
    path('', view=views.LocationsHomeView.as_view(), name='locations_home'),
    path('<int:pk>/', view=views.LocationsDetailView.as_view(), name='locations_detail'),
    #path('<int:pk>/<int:current_location>/', view=views.LocationsDetailView.as_view(), name='locations_detail'),
    path('add/', view=views.LocationsCreateView.as_view(), name='locations_add'),
    path('edit/<int:pk>/', view=views.LocationsUpdateView.as_view(), name='locations_update'),
    #path('edit/<int:pk>/<int:current_location>/', view=views.LocationsUpdateView.as_view(), name='locations_update'),
    path('delete/<int:pk>/', view=views.LocationsDeleteView.as_view(), name='locations_delete'),
    # AJAX paths
    path('ajax/load-navtree/', views.load_locations_navtree, name='ajax_load_locations_navtree'),
    path('ajax/detail/<int:pk>/', view=views.LocationsAjaxDetailView.as_view(), name='ajax_location_detail'),
    path('ajax/edit/<int:pk>/', view=views.LocationsAjaxUpdateView.as_view(), name='ajax_location_update'),
    path('ajax/add/', view=views.LocationsAjaxCreateView.as_view(), name='ajax_location_add'),
    path('ajax/delete/<int:pk>/', view=views.LocationsAjaxDeleteView.as_view(), name='ajax_location_delete'),
]
