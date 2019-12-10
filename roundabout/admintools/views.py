import csv
import io

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.db import IntegrityError
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .forms import PrinterForm, ImportInventoryForm
from .models import Printer, TempImport, TempImportItem
from roundabout.userdefinedfields.models import FieldValue, Field
from roundabout.inventory.models import Inventory
from roundabout.parts.models import Part

# Bulk Inventory Import Functions
# ------------------------------------------
# Create a blank CSV template for user to download and populate
class ImportInventoryCreateTemplateView(View):

    def get(self, request, *args, **kwargs):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        # Create default list of required fields
        headers = ['Serial Number', 'Part Number', 'Location', 'Notes']

        # Get all UDF fields for column names
        custom_fields = Field.objects.all()

        if custom_fields:
            for field in custom_fields:
                headers.append(field.field_name)

        writer = csv.writer(response)
        writer.writerow(headers)

        return response


# Upload formview for Inventory Bulk upload
class ImportInventoryUploadView(FormView):
    form_class = ImportInventoryForm
    template_name = 'admintools/import_inventory_upload_form.html'
    success_url = reverse_lazy('admintools:printers_home')

    def form_valid(self, form):
        csv_file = self.request.FILES['document']
        # Create or get parent TempImport object
        tempimport_obj, created = TempImport.objects.get_or_create(name=csv_file.name)
        # If already exists, reset all the related items
        if created:
            tempimport_obj.tempimportitems.all().delete()

        # Set up the Django file object for CSV DictReader
        csv_file.seek(0)
        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))

        for row in reader:
            data = {}
            # Loop through each row, run validation for different fields
            for key, value in row.items():
                print(key, value)
                if key == 'serial_number':
                    try:
                        item = Inventory.objects.get(serial_number=value.strip())
                    except Inventory.DoesNotExist:
                        item = None

                    if item:
                        data['serial_number'] = value.strip()
                    else:
                        data['serial_number'] = 'ERROR. Serial Number already exists'

                if key == 'part_number':
                    try:
                        part = Part.objects.get(part_number=value.strip())
                    except Part.DoesNotExist:
                        part = None

                    if item:
                        data['part_number'] = value.strip()
                    else:
                        data['part_number'] = 'ERROR. No matching Part Number'

                if key == 'Location':
                    try:
                        location = Location.objects.get(name=value.strip())
                    except Location.DoesNotExist:
                        location = None
                        print('No matching Location')

                    if item:
                        data['Location'] = value.strip()
                    else:
                        data['Location'] = 'ERROR. No matching Location'

                tempitem_obj = TempImportItem(data=data, tempimport=tempimport_obj)
                tempitem_obj.save()

        return super(ImportInventoryUploadView, self).form_valid(form)


# Printer functionality
# ----------------------

class PrinterListView(LoginRequiredMixin, ListView):
    model = Printer
    template_name = 'admintools/printer_list.html'
    context_object_name = 'printers'


class PrinterCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Printer
    form_class = PrinterForm
    context_object_name = 'printer'
    permission_required = 'admintools.add_printer'
    redirect_field_name = 'home'

    def get_success_url(self):
        return reverse('admintools:printers_home', )

class PrinterUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Printer
    form_class = PrinterForm
    context_object_name = 'printer'
    permission_required = 'admintools.add_printer'
    redirect_field_name = 'home'

    def get_success_url(self):
        return reverse('admintools:printers_home', )


class PrinterDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Printer
    success_url = reverse_lazy('admintools:printers_home')
    permission_required = 'admintools.delete_printer'
    redirect_field_name = 'home'
