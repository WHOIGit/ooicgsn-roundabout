from django.urls import path

from . import views

app_name = 'reports'
urlpatterns = [
    path('', view=views.ReportsHome.as_view(), name='reports_home'),
    path('build_report/<int:pk>/', view=views.BuildReport.as_view(), name='build_report'),
    path('build_report/csv/<int:pk>/', view=views.BuildReportCsvDownload.as_view(), name='build_report_csv'),
]
