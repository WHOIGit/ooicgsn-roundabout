import csv
import io
import json

from django.http import HttpResponse, HttpResponseRedirect
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
from roundabout.locations.models import Location

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

    def get_success_url(self):
        return reverse('admintools:import_inventory_preview_detail', args=(self.object.id,))

    def form_valid(self, form):
        csv_file = self.request.FILES['document']
        # Create or get parent TempImport object
        tempimport_obj, created = TempImport.objects.get_or_create(name=csv_file.name)
        # If already exists, reset all the related items
        if not created:
            tempimport_obj.tempimportitems.all().delete()

        # Set up the Django file object for CSV DictReader
        csv_file.seek(0)
        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))

        for row in reader:
            # Need to put this dictionary in a list to maintain column order
            data = []
            # Loop through each row, run validation for different fields
            for key, value in row.items():
                print(key, value)
                if key == 'Serial Number':
                    try:
                        item = Inventory.objects.get(serial_number=value.strip())
                    except Inventory.DoesNotExist:
                        item = None

                    if not item:
                        data.append({'serial_number': value.strip()})
                    else:
                        data.append({'serial_number': value + '<div class="alert alert-danger" role="alert">ERROR. Serial Number already exists</div>'})

                if key == 'Part Number':
                    try:
                        part = Part.objects.get(part_number=value.strip())
                    except Part.DoesNotExist:
                        part = None

                    if part:
                        data.append({'part_number': value.strip()})
                    else:
                        data.append({'part_number': value + '<div class="alert alert-danger" role="alert">ERROR. No matching Part Number</div>'})


                if key == 'Location':
                    try:
                        location = Location.objects.get(name=value.strip())
                    except Location.DoesNotExist:
                        location = None
                        print('No matching Location')

                    if location:
                        data.append({'location': value.strip()})
                    else:
                        data.append({'location': value + '<div class="alert alert-danger" role="alert">ERROR. No matching Location</div>'})

            print(data)
            tempitem_obj = TempImportItem(data=data, tempimport=tempimport_obj)
            tempitem_obj.save()

        #return super(ImportInventoryUploadView, self).form_valid(form)
        return HttpResponseRedirect(reverse('admintools:import_inventory_preview_detail', args=(tempimport_obj.id,)))

# Create a blank CSV template for user to download and populate
class ImportInventoryPreviewDetailView(DetailView):
    model = TempImport
    context_object_name = 'tempimport'
    template_name='admintools/import_tempimport_detail.html'


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
