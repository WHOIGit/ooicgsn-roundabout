import csv
import io
import json
import requests
from dateutil import parser

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.db import IntegrityError
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .forms import PrinterForm, ImportInventoryForm
from .models import *
from roundabout.userdefinedfields.models import FieldValue, Field
from roundabout.inventory.models import Inventory, Action
from roundabout.parts.models import Part, Revision
from roundabout.locations.models import Location
from roundabout.assemblies.models import AssemblyType, Assembly, AssemblyPart
from roundabout.assemblies.views import make_tree_copy

# Bulk Inventory Import Functions
# ------------------------------------------
# Create a blank CSV template for user to download and populate
class ImportInventoryCreateTemplateView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="roundabout-inventory-import-template.csv"'

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
class ImportInventoryUploadView(LoginRequiredMixin, FormView):
    form_class = ImportInventoryForm
    template_name = 'admintools/import_inventory_upload_form.html'

    def form_valid(self, form):
        csv_file = self.request.FILES['document']
        # Set up the Django file object for CSV DictReader
        csv_file.seek(0)
        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
        # Get the column headers to save with parent TempImport object
        headers = reader.fieldnames

        # Create or get parent TempImport object
        tempimport_obj, created = TempImport.objects.get_or_create(name=csv_file.name, column_headers=headers)
        # If already exists, reset all the related items
        if not created:
            tempimport_obj.tempimportitems.all().delete()

        for row in reader:
            # Need to put this dictionary in a list to maintain column order
            data = []
            # Loop through each row, run validation for different fields
            for key, value in row.items():
                if key == 'Serial Number':
                    # Check if Serial Number already being used
                    try:
                        item = Inventory.objects.get(serial_number=value.strip())
                        error_msg = "Serial Number already exists."
                    except Inventory.DoesNotExist:
                        item = None

                    if not item:
                        data.append({'field_name': key, 'field_value': value.strip(), 'error': False})
                    else:
                        data.append({'field_name': key, 'field_value': value.strip(), 'error': True, 'error_msg': error_msg})

                elif key == 'Part Number':
                    # Check if Part template exists
                    try:
                        part = Part.objects.get(part_number=value.strip())
                    except Part.DoesNotExist:
                        part = None
                        error_msg = "No matching Part Number. Check if Part Template exists."

                    if part:
                        data.append({'field_name': key, 'field_value': value.strip(), 'error': False})
                    else:
                        data.append({'field_name': key, 'field_value': value.strip(), 'error': True, 'error_msg': error_msg})

                elif key == 'Location':
                    # Check if Location exists and if there's multiple Locations with same name
                    locations = Location.objects.filter(name=value.strip())

                    if not locations:
                        location = None
                        error_msg = "No matching Location. Check if Location exists."
                    elif locations.count() > 1:
                        location = None
                        error_msg = "Multiple Locations with same name, destination is unclear. Rename Locations or change destination."
                    else:
                        # get Location object out of queryset
                        location = locations.first()

                    if location:
                        data.append({'field_name': key, 'field_value': value.strip(), 'error': False})
                    else:
                        data.append({'field_name': key, 'field_value': value.strip(), 'error': True, 'error_msg': error_msg})

                elif key == 'Notes':
                        data.append({'field_name': key, 'field_value': value.strip(), 'error': False})

                # Now run through all the Custom Fields, validate type, add to JSON
                else:
                    try:
                        custom_field = Field.objects.get(field_name=key)
                    except Field.DoesNotExist:
                        custom_field = None
                        error_msg = "No matching Custom Field. Check if Field exists."

                    if custom_field:
                        if value:
                            if custom_field.field_type == 'IntegerField':
                                try:
                                    value = int(value.strip())
                                    data.append({'field_name': key, 'field_value': value, 'error': False})
                                except ValueError:
                                    error_msg = "Validation Error. Needs to be an integer."
                                    data.append({'field_name': key, 'field_value': value, 'error': True, 'error_msg': error_msg})

                            elif custom_field.field_type == 'DecimalField':
                                try:
                                    value = float(value.strip())
                                    data.append({'field_name': key, 'field_value': value, 'error': False})
                                except ValueError:
                                    error_msg = "Validation Error. Needs to be a decimal."
                                    data.append({'field_name': key, 'field_value': value, 'error': True, 'error_msg': error_msg})

                            elif custom_field.field_type == 'BooleanField':
                                # function to check if various versions of Boolean pass
                                def check_if_bool(self, value):
                                    return value.lower() in ('yes', 'true', 't', '1', 'no', 'false', 'f', '0')

                                # function to translate various versions
                                def str_to_bool(self, value):
                                    return value.lower() in ('yes', 'true', 't', '1')

                                if check_if_bool(self, value.strip()):
                                    print('Boolean!')
                                    data.append({'field_name': key, 'field_value': str_to_bool(self, value.strip()), 'error': False})
                                else:
                                    error_msg = "Validation Error. Needs to be a True/False boolean."
                                    data.append({'field_name': key, 'field_value': value.strip(), 'error': True, 'error_msg': error_msg})

                            elif custom_field.field_type == 'DateField':
                                try:
                                    value = parser.parse(value.strip())
                                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                                    data.append({'field_name': key, 'field_value': value, 'error': False})
                                except:
                                    error_msg = "Validation Error. Needs to be a valid Date Format (ex. mm/dd/yyyy)."
                                    data.append({'field_name': key, 'field_value': value, 'error': True, 'error_msg': error_msg})
                            else:
                                data.append({'field_name': key, 'field_value': value, 'error': False})
                        else:
                            # Add blank value for empty value columns to keep table structure
                            data.append({'field_name': key, 'field_value': value, 'error': False})
                    else:
                        data.append({'field_name': key, 'field_value': value, 'error': True, 'error_msg': error_msg})

            tempitem_obj = TempImportItem(data=data, tempimport=tempimport_obj)
            tempitem_obj.save()
            self.tempimport_obj = tempimport_obj

        return super(ImportInventoryUploadView, self).form_valid(form)

    def get_success_url(self):
        return reverse('admintools:import_inventory_preview_detail', args=(self.tempimport_obj.id,))


# DetailView for the Temporary Import data saved in TempImport model
class ImportInventoryPreviewDetailView(LoginRequiredMixin, DetailView):
    model = TempImport
    context_object_name = 'tempimport'
    template_name='admintools/import_tempimport_detail.html'

    def get_context_data(self, **kwargs):
        context = super(ImportInventoryPreviewDetailView, self).get_context_data(**kwargs)
        # Need to check if any errors exist in the upload so we can disable next step if necessary
        importitems_qs = self.object.tempimportitems.all()
        # set default validation status
        valid_upload = True

        for item_obj in importitems_qs:
            for data in item_obj.data:
                # if any error exists, set validation status and break loop
                if data['error']:
                    valid_upload = False
                    break

        context.update({
            'valid_upload': valid_upload
        })
        return context


# Complete the import process after successful Preview step
class ImportInventoryUploadAddActionView(LoginRequiredMixin, RedirectView):
    permanent = False
    query_string = False

    def get_redirect_url(self, *args, **kwargs):
        try:
            tempimport_obj = TempImport.objects.get(id=self.kwargs['pk'])
        except:
            tempimport_obj = None

        if tempimport_obj:
            # get all the Inventory items to upload from the Temp tables
            for item_obj in tempimport_obj.tempimportitems.all():
                inventory_obj = Inventory()

                for col in item_obj.data:
                    if col['field_name'] == 'Serial Number':
                        inventory_obj.serial_number = col['field_value']
                    elif col['field_name'] == 'Part Number':
                        part = Part.objects.get(part_number=col['field_value'])
                        revision = part.revisions.last()
                        inventory_obj.part = part
                        inventory_obj.revision = revision
                    elif col['field_name'] == 'Location':
                        location = Location.objects.get(name=col['field_value'])
                        inventory_obj.location = location
                    elif col['field_name'] == 'Notes':
                        note_detail = col['field_value']

                inventory_obj.save()
                # Create initial history record for item
                action_record = Action.objects.create(action_type='invadd',
                                                      detail='Item first added to Inventory by Bulk Import',
                                                      location=location,
                                                      user=self.request.user,
                                                      inventory=inventory_obj)

                # Create notes history record for item
                if note_detail:
                    note_record = Action.objects.create(action_type='note',
                                                          detail=note_detail,
                                                          location=location,
                                                          user=self.request.user,
                                                          inventory=inventory_obj)

                # Add the Custom Fields
                for col in item_obj.data:
                    if not col['field_name'] == 'Serial Number' and not col['field_name'] == 'Part Number' and not col['field_name'] == 'Location' and not col['field_name'] == 'Notes':
                        # Get the field
                        try:
                            custom_field = Field.objects.get(field_name=col['field_name'])
                        except Field.DoesNotExist:
                            custom_field = None

                        # Create new value object
                        if col['field_value']:
                            if custom_field:
                                fieldvalue = FieldValue.objects.create(field=custom_field,
                                                                       field_value=col['field_value'],
                                                                       inventory=inventory_obj,
                                                                       is_current=True,
                                                                       user=self.request.user)
                            else:
                                # Drop any fields that don't match a custom field into a History Note
                                note_detail = col['field_name'] + ': ' + col['field_value']
                                note_record = Action.objects.create(action_type='note',
                                                                      detail=note_detail,
                                                                      location=location,
                                                                      user=self.request.user,
                                                                      inventory=inventory_obj)

        return reverse('admintools:import_inventory_upload_success', )


class ImportInventoryUploadSuccessView(TemplateView):
    template_name = "admintools/import_inventory_upload_success.html"


# Assembly Template import tool
# Import an existing Assembly template from a separate RDB instance

# View to make API request to a separate RDB instance and copy an Assembly Template
class ImportAssemblyAPIRequestCopyView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'assemblies.add_assembly'

    def get(self, request, *args, **kwargs):
        # Get the Assembly data from RDB API
        request_url = 'https://rdb-demo.whoi.edu/api/v1/assemblies/14/'
        assembly_request = requests.get(request_url, verify=False)
        new_assembly = assembly_request.json()
        # Get or create new parent Temp Assembly
        temp_assembly_obj, created = TempImportAssembly.objects.get_or_create(name=new_assembly['name'],
                                                                              assembly_number=new_assembly['assembly_number'],
                                                                              description=new_assembly['description'],)
        # If already exists, reset all the related items
        if not created:
            temp_assembly_obj.temp_assembly_parts.all().delete()

        try:
            assembly_type = AssemblyType.objects.get(name=new_assembly['assembly_type']['name'])
            import_error = False
        except AssemblyType.DoesNotExist:
            assembly_type = None
            import_error = True
            import_error_msg = 'Assembly Type does not exist in this RDB. Please add it, and try again.'

        if not import_error:
            # add Assembly Type to the parent object
            temp_assembly_obj.assembly_type = assembly_type
            temp_assembly_obj.save()

            # import all Assembly Parts to temp table
            for assembly_part in new_assembly['assembly_parts']:
                # Need to validate that the Part template exists
                try:
                    part = Part.objects.get(part_number=assembly_part['part']['part_number'])
                except Part.DoesNotExist:
                    part = None
                    import_error = True
                    import_error_msg = 'Part Number does not exist in this RDB. Please add Part Template, and try again.'

                if not import_error:
                    temp_assembly_part_obj = TempImportAssemblyPart(assembly=temp_assembly_obj,
                                                                    part=part,
                                                                    previous_id=assembly_part['id'],
                                                                    previous_parent=assembly_part['parent'],
                                                                    note=assembly_part['note'],
                                                                    order=assembly_part['order'])
                    temp_assembly_part_obj.save()
                    print(temp_assembly_part_obj)

            # run through the temp Assembly Parts again to set the correct Parent structure for MPTT
            for temp_assembly_part in temp_assembly_obj.temp_assembly_parts.all():
                # Check if there's a previous_parent, if so we need to find the correct new object
                if temp_assembly_part.previous_parent:
                    parent_obj = TempImportAssemblyPart.objects.get(previous_id=temp_assembly_part.previous_parent)
                    temp_assembly_part.parent = parent_obj
                    temp_assembly_part.save()

            # Rebuild the TempImportAssemblyPart MPTT tree to ensure correct structure for copying
            TempImportAssemblyPart._tree_manager.rebuild()

            # copy the Temp Assembly to real destination table
            assembly_obj = Assembly(name=temp_assembly_obj.name,
                                    assembly_type=temp_assembly_obj.assembly_type,
                                    assembly_number=temp_assembly_obj.assembly_number,
                                    description=temp_assembly_obj.description)
            assembly_obj.save()

            temp_assembly_root_part = temp_assembly_obj.temp_assembly_parts.first().get_root()

            make_tree_copy(temp_assembly_root_part, assembly_obj, temp_assembly_root_part.parent)

        return HttpResponse('<h1>New Assembly Template Imported!</h1>')


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
