"""
# Copyright (C) 2019-2020 Woods Hole Oceanographic Institution
#
# This file is part of the Roundabout Database project ("RDB" or
# "ooicgsn-roundabout").
#
# ooicgsn-roundabout is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# ooicgsn-roundabout is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ooicgsn-roundabout in the COPYING.md file at the project root.
# If not, see <http://www.gnu.org/licenses/>.
"""

import csv
import io
import json
import requests
from dateutil import parser
import datetime
from types import SimpleNamespace

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


from .forms import PrinterForm, ImportInventoryForm, ImportCalibrationForm
from .models import *
from roundabout.userdefinedfields.models import FieldValue, Field
from roundabout.inventory.models import Inventory, Action
from roundabout.parts.models import Part, Revision, Documentation, PartType
from roundabout.locations.models import Location
from roundabout.assemblies.models import AssemblyType, Assembly, AssemblyPart, AssemblyRevision
from roundabout.assemblies.views import _make_tree_copy
from roundabout.inventory.utils import _create_action_history
from roundabout.calibrations.models import CoefficientName, CoefficientValueSet, CalibrationEvent
from roundabout.calibrations.forms import validate_coeff_vals, parse_valid_coeff_vals
from roundabout.users.models import User


# Test URL for Sentry.io logging
def trigger_error(request):
    division_by_zero = 1 / 0


# CSV File Uploader for GitHub Calibration Coefficients
class ImportCalibrationsUploadView(LoginRequiredMixin, FormView):
    form_class = ImportCalibrationForm
    template_name = 'admintools/import_calibrations_upload_form.html'

    def form_valid(self, form):
        cal_files = self.request.FILES.getlist('cal_csv')
        for cal_csv in cal_files:
            ext = cal_csv.name[-3:]
            if ext == 'ext':
                continue
            if ext == 'csv':
                cal_csv.seek(0)
                reader = csv.DictReader(io.StringIO(cal_csv.read().decode('utf-8')))
                headers = reader.fieldnames
                coeff_val_sets = []
                inv_serial = cal_csv.name.split('__')[0]
                cal_date_string = cal_csv.name.split('__')[1][:8]
                inventory_item = Inventory.objects.get(serial_number=inv_serial)
                cal_date_date = datetime.datetime.strptime(cal_date_string, "%Y%m%d").date()
                csv_event = CalibrationEvent.objects.create(
                    calibration_date = cal_date_date,
                    inventory = inventory_item
                )
                for idx, row in enumerate(reader):
                    row_data = row.items()
                    for key, value in row_data:
                        if key == 'name':
                            calibration_name = value.strip()
                            cal_name_item = CoefficientName.objects.get(
                                calibration_name = calibration_name,
                                coeff_name_event =  inventory_item.part.coefficient_name_events.first()
                            )
                        elif key == 'value':
                            valset_keys = {'cal_dec_places': inventory_item.part.cal_dec_places}
                            mock_valset_instance = SimpleNamespace(**valset_keys)
                            raw_valset = str(value)
                            if '[' in raw_valset:
                                raw_valset = raw_valset[1:-1]
                            if 'SheetRef' in raw_valset:
                                for file in cal_files:
                                    file.seek(0)
                                    file_extension = file.name[-3:]
                                    if file_extension == 'ext':
                                        cal_ext_split = file.name.split('__')
                                        inv_ext_serial = cal_ext_split[0]
                                        cal_ext_date = cal_ext_split[1]
                                        cal_ext_name = cal_ext_split[2][:-4]
                                        if (inv_ext_serial == inv_serial) and (cal_ext_date == cal_date_string) and (cal_ext_name == calibration_name):
                                            reader = io.StringIO(file.read().decode('utf-8'))
                                            contents = reader.getvalue()
                                            raw_valset = contents
                            validate_coeff_vals(mock_valset_instance, cal_name_item.value_set_type, raw_valset)
                        elif key == 'notes':
                            notes = value.strip()
                            coeff_val_set = CoefficientValueSet(
                                coefficient_name = cal_name_item,
                                value_set = raw_valset,
                                notes = notes
                            )
                            coeff_val_sets.append(coeff_val_set)
                if form.cleaned_data['user_draft'].exists():
                    draft_users = form.cleaned_data['user_draft']
                    for user in draft_users:
                        csv_event.user_draft.add(user)
                for valset in coeff_val_sets:
                    valset.calibration_event = csv_event
                    valset.save()
                    parse_valid_coeff_vals(valset)
                _create_action_history(csv_event, Action.CALCSVIMPORT, self.request.user)
        return super(ImportCalibrationsUploadView, self).form_valid(form)

    def get_success_url(self):
        return reverse('admintools:import_inventory_upload_success', )

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
                        if value and not value.isspace():
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
                    # Split the field on "|" delimiter to add multiple Notes
                    note_list = note_detail.split('|')
                    for note in note_list:
                        if note:
                            note_record = Action.objects.create(action_type='note',
                                                                  detail=note,
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
# Makes a copy of the Assembly Revisiontree starting at "root_part",
# move to new Revision, reparenting it to "parent"
def _make_revision_tree_copy(root_part, new_revision, parent=None):
    new_ap = AssemblyPart.objects.create(assembly_revision=new_revision, part=root_part.part, parent=parent, order=root_part.order)

    for child in root_part.get_children():
        _make_revision_tree_copy(child, new_revision, new_ap)

def _api_import_assembly_parts_tree(root_part_url, new_revision, parent=None):
    api_token = '7cd558ee6880982d08669c08b7f92a505f0847fb'
    headers = {
        'Authorization': 'Token ' + api_token,
    }
    params = {'expand': 'part'}
    assembly_part_request = requests.get(root_part_url, params=params, headers=headers, verify=False)
    assembly_part_data = assembly_part_request.json()
    # Need to validate that the Part template exists before creating AssemblyPart
    try:
        part_obj = Part.objects.get(part_number=assembly_part_data['part']['part_number'])
    except Part.DoesNotExist:
        params = {'expand': 'part_type,revisions.documentation'}
        part_request = requests.get(assembly_part_data['part']['url'], params=params, headers=headers, verify=False)
        part_data = part_request.json()
        print(part_data)
        part_obj = Part.objects.create(
            name = part_data['name'],
            friendly_name = part_data['friendly_name'],
            part_type_id = part_data['part_type']['id'],
            part_number = part_data['part_number'],
            unit_cost = part_data['unit_cost'],
            refurbishment_cost = part_data['refurbishment_cost'],
            note = part_data['note'],
            cal_dec_places = part_data['cal_dec_places'],
        )
        # Create all Revisions objects for this Part
        for revision in part_data['revisions']:
            revision_obj = Revision.objects.create(
                revision_code = revision['revision_code'],
                unit_cost = revision['unit_cost'],
                refurbishment_cost = revision['refurbishment_cost'],
                created_at = revision['created_at'],
                part = part_obj,
            )
            # Create all Documentation objects for this Revision
            for doc in revision['documentation']:
                doc_obj = Documentation.objects.create(
                    name = doc['name'],
                    doc_type = doc['doc_type'],
                    doc_link =  doc['doc_link'],
                    revision = revision_obj,
                )
    # Now create the Assembly Part
    assembly_part_obj = AssemblyPart.objects.create(
        assembly_revision = new_revision,
        part = part_obj,
        parent=parent,
        note = assembly_part_data['note'],
        order = assembly_part_data['order']
    )
    # Loop through the tree
    for child_url in assembly_part_data['children']:
        _api_import_assembly_parts_tree(child_url, new_revision, assembly_part_obj)

    return True


# View to make API request to a separate RDB instance and copy an Assembly Template
class ImportAssemblyAPIRequestCopyView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'assemblies.add_assembly'

    def get(self, request, *args, **kwargs):
        api_token = '7cd558ee6880982d08669c08b7f92a505f0847fb'
        headers = {
            'Authorization': 'Token ' + api_token,
        }
        params = {'expand': 'assembly_type,assembly_revisions'}
        # Get the Assembly data from RDB API
        request_url = 'https://rdb-testing.whoi.edu/api/v1/assembly-templates/assemblies/31/'
        assembly_request = requests.get(request_url, params=params, headers=headers, verify=False)
        new_assembly = assembly_request.json()
        # Get or create new parent Temp Assembly
        assembly_obj, created = Assembly.objects.get_or_create(name=new_assembly['name'],
                                                               assembly_number=new_assembly['assembly_number'],
                                                               description=new_assembly['description'],)
        print(assembly_obj)
        try:
            assembly_type = AssemblyType.objects.get(name=new_assembly['assembly_type']['name'])
        except AssemblyType.DoesNotExist:
            # No matching AssemblyType, add it from the API request data
            assembly_type = AssemblyType.objects.create(name=new_assembly['assembly_type']['name'])
        print(assembly_type)
        assembly_obj.assembly_type = assembly_type
        assembly_obj.save()

        # Create all Revisions
        for rev in new_assembly['assembly_revisions']:
            assembly_revision_obj = AssemblyRevision.objects.create(
                revision_code = rev['revision_code'],
                revision_note = rev['revision_note'],
                created_at = rev['created_at'],
                assembly = assembly_obj,
            )
            print(assembly_revision_obj)

            for root_url in rev['assembly_parts_roots']:
                tree_created = _api_import_assembly_parts_tree(root_url, assembly_revision_obj)

            print(tree_created)
            #AssemblyPart._tree_manager.rebuild()
        return HttpResponse('<h1>New Assembly Template Imported! - %s</h1>' % (assembly_obj))


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
