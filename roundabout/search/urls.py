from django.urls import path

from . import views

app_name = 'search'
urlpatterns = [
    path('', view=views.BasicSearch.as_view(), name='basic'),
    #path('csv/<str:qs>',view=views.basicCsvDownload.as_view(), name='basic-csv'),
    path('adv', view=views.AdvSearch.as_view(), name='adv'),
    path('csv/<str:adv_or_basic>/<str:qs>', view=views.CsvDownloadSearch.as_view(), name='csv'),

]
