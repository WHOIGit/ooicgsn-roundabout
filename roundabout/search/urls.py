from django.urls import path

from . import views

app_name = 'reports'
urlpatterns = [
    #path('', view=views.SearchHome.as_view(), name='search_home'),
    path('searchbar/', view=views.SearchList.as_view(), name='searchbar'),
]
