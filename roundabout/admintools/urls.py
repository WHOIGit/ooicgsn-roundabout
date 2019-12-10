from django.urls import path

from . import views

app_name = 'admintools'
urlpatterns = [
    # Printers
    path('printers/', view=views.PrinterListView.as_view(), name='printers_home'),
    path('printers/add/', view=views.PrinterCreateView.as_view(), name='printers_add'),
    path('printers/edit/<int:pk>/', view=views.PrinterUpdateView.as_view(), name='printers_update'),
    path('printers/delete/<int:pk>/', view=views.PrinterDeleteView.as_view(), name='printers_delete'),
    # Import tool
    path('import/inventory/create-template/', view=views.ImportInventoryCreateTemplateView.as_view(), name='import_inventory_create_template'),
    path('import/inventory/upload/', view=views.ImportInventoryUploadView.as_view(), name='import_inventory_upload'),
]
