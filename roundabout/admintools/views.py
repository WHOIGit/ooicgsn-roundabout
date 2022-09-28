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
import datetime
import io
from types import SimpleNamespace

import requests
from dateutil import parser
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
)
from roundabout.assemblies.models import Assembly, AssemblyPart, AssemblyRevision
from roundabout.calibrations.forms import parse_valid_coeff_vals
from roundabout.calibrations.models import CoefficientName, CoefficientValueSet, CalibrationEvent
from roundabout.inventory.models import Inventory, Action
from roundabout.inventory.utils import _create_action_history
from roundabout.locations.models import Location
from roundabout.parts.models import Revision, Documentation, PartType
from roundabout.userdefinedfields.models import FieldValue, Field
from roundabout.configs_constants.models import *
from roundabout.users.models import User
from .forms import PrinterForm, ImportInventoryForm, ImportCalibrationForm
from .models import *


# Test URL for Sentry.io logging
def trigger_error(request):
    division_by_zero = 1 / 0


def parse_cal_file(self, form, cal_csv, ext_files):
    cal_csv_filename = cal_csv.name[:-4]
    cal_csv.seek(0)
    reader = csv.DictReader(io.StringIO(cal_csv.read().decode('utf-8')))
    headers = reader.fieldnames
    coeff_val_sets = []
    inv_serial = cal_csv.name.split('__')[0]
    cal_date_string = cal_csv.name.split('__')[1][:8]
    inventory_item = Inventory.objects.get(serial_number=inv_serial)
    cal_date_date = datetime.datetime.strptime(cal_date_string, "%Y%m%d").date()
    csv_event = CalibrationEvent.objects.create(
        calibration_date=cal_date_date,
        inventory=inventory_item
    )
    for idx, row in enumerate(reader):
        row_data = row.items()
        for key, value in row_data:
            if key == 'name':
                calibration_name = value.strip()
                cal_name_item = CoefficientName.objects.get(
                    calibration_name=calibration_name,
                    coeff_name_event=inventory_item.part.part_confignameevents.first()
                )
            elif key == 'value':
                valset_keys = {'cal_dec_places': inventory_item.part.cal_dec_places}
                mock_valset_instance = SimpleNamespace(**valset_keys)
                raw_valset = str(value)
                if '[' in raw_valset:
                    raw_valset = raw_valset[1:-1]
                if 'SheetRef' in raw_valset:
                    ext_finder_filename = "__".join((cal_csv_filename, calibration_name))
                    ref_file = [file for file in ext_files if ext_finder_filename in file.name][0]
                    ref_file.seek(0)
                    reader = io.StringIO(ref_file.read().decode('utf-8'))
                    contents = reader.getvalue()
                    raw_valset = contents
            elif key == 'notes':
                notes = value.strip()
                coeff_val_set = CoefficientValueSet(
                    coefficient_name=cal_name_item,
                    value_set=raw_valset,
                    notes=notes
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


# CSV File Uploader for GitHub Calibration Coefficients
class ImportCalibrationsUploadView(LoginRequiredMixin, FormView):
    form_class = ImportCalibrationForm
    template_name = 'admintools/import_calibrations_upload_form.html'

    def form_valid(self, form):
        cal_files = self.request.FILES.getlist('cal_csv')
        csv_files = []
        ext_files = []
        for file in cal_files:
            ext = file.name[-3:]
            if ext == 'ext':
                ext_files.append(file)
            if ext == 'csv':
                csv_files.append(file)
        for cal_csv in csv_files:
            parse_cal_file(self, form, cal_csv, ext_files)
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
        update_existing_inventory = form.cleaned_data.get('update_existing_inventory')
        # Set up the Django file object for CSV DictReader
        csv_file.seek(0)
        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
        # Get the column headers to save with parent TempImport object
        headers = reader.fieldnames

        # Create or get parent TempImport object
        tempimport_obj, created = TempImport.objects.get_or_create(name=csv_file.name, column_headers=headers)
        if update_existing_inventory:
            tempimport_obj.update_existing_inventory = True
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

                    if update_existing_inventory:
                        if item:
                            data.append({'field_name': key, 'field_value': value.strip(), 'error': False})
                        else:
                            error_msg = "Matching Serial Number not found"
                            data.append({'field_name': key, 'field_value': value.strip(), 'error': True, 'error_msg': error_msg})
                    else:
                        if not item:
                            data.append({'field_name': key, 'field_value': value.strip(), 'error': False})
                        else:
                            data.append({'field_name': key, 'field_value': value.strip(),
                                        'error': True, 'error_msg': error_msg})

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
                        data.append({'field_name': key, 'field_value': value.strip(),
                                    'error': True, 'error_msg': error_msg})

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

                    if update_existing_inventory:
                        if location:
                            data.append({'field_name': key, 'field_value': value.strip(), 'error': False})
                            if item:
                                if item.location != location and hasattr(item,'build'):
                                    if item.build != None:
                                        error_msg = "Bulk Import cannot change Locations of Deployed Inventory."
                                        data.append({'field_name': key, 'field_value': value.strip(), 'error': True, 'warning': False, 'error_msg': error_msg})
                                        
                    else:
                        if location:
                            data.append({'field_name': key, 'field_value': value.strip(), 'error': False})
                        else:
                            data.append({'field_name': key, 'field_value': value.strip(),
                                        'error': True, 'error_msg': error_msg})

                elif key == 'Notes':
                    if value is not None:
                        data.append({'field_name': key, 'field_value': value.strip(), 'error': False})
                    else:
                        data.append({'field_name': key, 'field_value': '', 'error': False})

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
                                    data.append({'field_name': key, 'field_value': value,
                                                'error': True, 'error_msg': error_msg})

                            elif custom_field.field_type == 'DecimalField':
                                try:
                                    value = float(value.strip())
                                    data.append({'field_name': key, 'field_value': value, 'error': False})
                                except ValueError:
                                    error_msg = "Validation Error. Needs to be a decimal."
                                    data.append({'field_name': key, 'field_value': value,
                                                'error': True, 'error_msg': error_msg})

                            elif custom_field.field_type == 'BooleanField':
                                # function to check if various versions of Boolean pass
                                def check_if_bool(self, value):
                                    return value.lower() in ('yes', 'true', 't', '1', 'no', 'false', 'f', '0')

                                # function to translate various versions
                                def str_to_bool(self, value):
                                    return value.lower() in ('yes', 'true', 't', '1')

                                if check_if_bool(self, value.strip()):
                                    print('Boolean!')
                                    data.append({'field_name': key, 'field_value': str_to_bool(
                                        self, value.strip()), 'error': False})
                                else:
                                    error_msg = "Validation Error. Needs to be a True/False boolean."
                                    data.append({'field_name': key, 'field_value': value.strip(),
                                                'error': True, 'error_msg': error_msg})

                            elif custom_field.field_type == 'DateField':
                                try:
                                    value = parser.parse(value.strip())
                                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                                    data.append({'field_name': key, 'field_value': value, 'error': False})
                                except:
                                    error_msg = "Validation Error. Needs to be a valid Date Format (ex. mm/dd/yyyy)."
                                    data.append({'field_name': key, 'field_value': value,
                                                'error': True, 'error_msg': error_msg})
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
            tempimport_obj.save()

        return super(ImportInventoryUploadView, self).form_valid(form)

    def get_success_url(self):
        return reverse('admintools:import_inventory_preview_detail', args=(self.tempimport_obj.id,))


# DetailView for the Temporary Import data saved in TempImport model
class ImportInventoryPreviewDetailView(LoginRequiredMixin, DetailView):
    model = TempImport
    context_object_name = 'tempimport'
    template_name = 'admintools/import_tempimport_detail.html'

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
            # get all the Inventory items to upload from the Temp tables2
            for item_obj in tempimport_obj.tempimportitems.all():
                inventory_obj = Inventory()

                note_detail = None

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

                inv_existing, inv_created = Inventory.objects.get_or_create(
                    serial_number=inventory_obj.serial_number, 
                    part=inventory_obj.part
                )
                
                if inv_created:
                    inv_existing.location = inventory_obj.location
                    inv_existing.save()
                else:
                    #   If build, Remove from build
					#   If deployed, end deployment
				    #   Change location
                    if tempimport_obj.update_existing_inventory:
                        print('Update Existing Inventory')
                        if inv_existing.location != inventory_obj.location:
                            print('Change Location')
                            if hasattr(inv_existing, 'build'):
                                print('existing build')
                                if inv_existing.build is not None:
                                    print('get current deployment')
                                    current_dep = inv_existing.build.current_deployment()
                                    if current_dep:
                                        print('build is deployed')
                                        current_dep.deployment_recovery_date = datetime.datetime.now()
                                        current_dep.deployment_retire_date = datetime.datetime.now()
                                        recover_record = Action.objects.create(
                                            action_type='deploymentrecover',
                                            detail = "%s Recovered to: %s. " % (current_dep.deployment_number, current_dep.location),
                                        )
                                        retire_record = Action.objects.create(
                                            action_type='deploymentretire',
                                            detail = "%s Ended." % (current_dep.deployment_number),
                                        )
                                        build = inv_existing.build
                                        build.detail = "%s Recovered to: %s. " % (current_dep.deployment_number, current_dep.location)
                                        build.save()
                                        build_recover = _create_action_history(build, 'deploymentrecover', self.request.user, None, "", datetime.datetime.now())
                                        build.detail = "%s Ended." % (current_dep.deployment_number)
                                        build.location = current_dep.location
                                        build.is_deployed = False
                                        build.save()
                                        build_retire = _create_action_history(build, 'deploymentretire', self.request.user, None, "", datetime.datetime.now())
                                        build_recover.cruise = current_dep.cruise_recovered or None
                                        build_retire.cruise = current_dep.cruise_recovered or None
                                        build_recover.save()
                                        build_retire.save()
                                        inv_existing.build = None
                                        inv_existing.location = inventory_obj.location
                                        inv_existing.save()
                                        _create_action_history(inv_existing, 'locationchange', self.request.user, None, "", datetime.datetime.now())
                                        print('inventory location changed')
                                    else:
                                        print('build is not deployed or no current deployed build')
                                        inv_existing.build = None
                                        inv_existing.location = inventory_obj.location
                                        _create_action_history(inv_existing, 'locationchange', self.request.user, None, "", datetime.datetime.now())
                                        inv_existing.save()
                                        print('inventory location changed')
                                else:
                                    print('build is not deployed or no current deployed build')
                                    inv_existing.build = None
                                    inv_existing.location = inventory_obj.location
                                    _create_action_history(inv_existing, 'locationchange', self.request.user, None, "", datetime.datetime.now())
                                    inv_existing.save()
                                    print('inventory location changed')

                inventory_obj = inv_existing
                # Create initial history record for item

                if tempimport_obj.update_existing_inventory:
                    action_record = Action.objects.create(action_type='invchange',
                                                    detail='Inventory item updated by Bulk Import',
                                                    location=inventory_obj.location,
                                                    user=self.request.user,
                                                    inventory=inventory_obj)
                else:
                    action_record = Action.objects.create(action_type='invadd',
                                                    detail='Item first added to Inventory by Bulk Import',
                                                    location=inventory_obj.location,
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
                                fieldvalue = FieldValue.objects.update_or_create(
                                    field=custom_field,
                                    inventory=inventory_obj,
                                    is_current=True,
                                    defaults = {
                                        'field_value': col['field_value'],
                                        'user': self.request.user,
                                    }
                                )
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
# Makes a copy of the Assembly Revision tree starting at "root_part",
# move to new Revision, reparenting it to "parent"
def _api_import_assembly_parts_tree(headers, root_part_url, new_revision, parent=None, importing_user=None):
    params = {'expand': 'part,assemblypart_configdefaultevents.config_defaults,assemblypart_configdefaultevents.config_defaults.config_name,assemblypart_configdefaultevents.user_draft,assemblypart_configdefaultevents.user_approver,assemblypart_configdefaultevents.actions.user'}
    assembly_part_request = requests.get(root_part_url, params=params, headers=headers, verify=False)
    assembly_part_data = assembly_part_request.json()
    # Need to validate that the Part template exists before creating AssemblyPart
    try:
        part_obj = Part.objects.get(part_number=assembly_part_data['part']['part_number'])

        if assembly_part_data['part']['part_confignameevents']:
            # Check if local Part has all current Config Names: ConfigNameEvent -> ConfigName(s)
            # First get existing Parts list of ConfigNames
            existing_config_names = []
            config_events_qs = part_obj.part_confignameevents.all()

            if config_events_qs:
                for config_event in config_events_qs:
                    config_names = list(config_event.config_names.values_list('name', flat=True))
                    existing_config_names = existing_config_names + config_names

            # Then check against the importing RDB instance's list of config names
            params = {'expand': 'part_confignameevents.config_names,part_confignameevents.user_draft,part_confignameevents.user_approver,part_confignameevents.actions.user'}
            part_configs_request = requests.get(
                assembly_part_data['part']['url'], params=params, headers=headers, verify=False)
            part_configs_data = part_configs_request.json()

            if part_configs_data['part_confignameevents']:
                importing_config_names = []
                for config_event in part_configs_data['part_confignameevents']:
                    missing_config_names = [config_name for config_name in config_event['config_names']
                                            if config_name['name'] not in existing_config_names]
                    print(missing_config_names)

                    if missing_config_names:
                        # create ConfigNameEvent parent object
                        config_event_obj = ConfigNameEvent.objects.create(
                            created_at=config_event['created_at'],
                            updated_at=config_event['updated_at'],
                            part=part_obj,
                            approved=config_event['approved'],
                            detail=config_event['detail'],
                        )

                        # get Users for draft/approval fields. Use importing User if no match
                        for user in config_event['user_draft']:
                            try:
                                user_obj = User.objects.get(username=user['username'])
                            except User.DoesNotExist:
                                user_obj = importing_user
                            # add to ManyToManyField
                            config_event_obj.user_draft.add(user_obj)

                        for user in config_event['user_approver']:
                            try:
                                user_obj = User.objects.get(username=user['username'])
                            except User.DoesNotExist:
                                user_obj = importing_user
                            # add to ManyToManyField
                            config_event_obj.user_approver.add(user_obj)

                        for config_name in missing_config_names:
                            # Create Missing Config Names
                            config_name_obj = ConfigName.objects.create(
                                part=part_obj,
                                config_name_event=config_event_obj,
                                name=config_name['name'],
                                config_type=config_name['config_type'],
                                created_at=config_name['created_at'],
                                deprecated=config_name['deprecated'],
                                include_with_calibrations=config_name['include_with_calibrations'],
                            )
                        # add Action history for this event
                        for action in config_event['actions']:
                            # get User for Action. Use importing User if no match
                            try:
                                user_obj = User.objects.get(username=action['user']['username'])
                            except User.DoesNotExist:
                                user_obj = importing_user

                            action_obj = Action.objects.create(
                                config_name_event=config_event_obj,
                                action_type=action['action_type'],
                                object_type=action['object_type'],
                                created_at=action['created_at'],
                                detail=action['detail'],
                                user=user_obj
                            )

    except Part.DoesNotExist:
        params = {'expand': 'part_type,revisions.documentation,part_confignameevents.config_names,part_confignameevents.user_draft,part_confignameevents.user_approver,part_confignameevents.actions.user'}
        part_request = requests.get(assembly_part_data['part']['url'], params=params, headers=headers, verify=False)
        part_data = part_request.json()

        try:
            part_type = PartType.objects.get(name=part_data['part_type']['name'])
        except PartType.DoesNotExist:
            # No matching AssemblyType, add it from the API request data
            part_type = PartType.objects.create(name=part_data['part_type']['name'])

        part_obj = Part.objects.create(
            name=part_data['name'],
            friendly_name=part_data['friendly_name'],
            part_type=part_type,
            part_number=part_data['part_number'],
            unit_cost=part_data['unit_cost'],
            refurbishment_cost=part_data['refurbishment_cost'],
            note=part_data['note'],
            cal_dec_places=part_data['cal_dec_places'],
        )
        # Create all Revisions objects for this Part
        for revision in part_data['revisions']:
            revision_obj = Revision.objects.create(
                revision_code=revision['revision_code'],
                unit_cost=revision['unit_cost'],
                refurbishment_cost=revision['refurbishment_cost'],
                created_at=revision['created_at'],
                part=part_obj,
            )
            # Create all Documentation objects for this Revision
            for doc in revision['documentation']:
                doc_obj = Documentation.objects.create(
                    name=doc['name'],
                    doc_type=doc['doc_type'],
                    doc_link=doc['doc_link'],
                    revision=revision_obj,
                )

        # Import all existing ConfigEvents/ConfigName
        if part_data['part_confignameevents']:
            for config_event in part_data['part_confignameevents']:
                config_event_obj = ConfigNameEvent.objects.create(
                    created_at=config_event['created_at'],
                    updated_at=config_event['updated_at'],
                    part=part_obj,
                    approved=config_event['approved'],
                    detail=config_event['detail'],
                )

                # get Users for draft/approval fields. Use importing User if no match
                for user in config_event['user_draft']:
                    try:
                        user_obj = User.objects.get(username=user['username'])
                    except User.DoesNotExist:
                        user_obj = importing_user
                    # add to ManyToManyField
                    config_event_obj.user_draft.add(user_obj)

                for user in config_event['user_approver']:
                    try:
                        user_obj = User.objects.get(username=user['username'])
                    except User.DoesNotExist:
                        user_obj = importing_user
                    # add to ManyToManyField
                    config_event_obj.user_approver.add(user_obj)

                for config_name in config_event['config_names']:
                    # Create All Config Names
                    config_name_obj = ConfigName.objects.create(
                        part=part_obj,
                        config_name_event=config_event_obj,
                        name=config_name['name'],
                        config_type=config_name['config_type'],
                        created_at=config_name['created_at'],
                        deprecated=config_name['deprecated'],
                        include_with_calibrations=config_name['include_with_calibrations'],
                    )

                # add Action history for this event
                for action in config_event['actions']:
                    # get User for Action. Use importing User if no match
                    try:
                        user_obj = User.objects.get(username=action['user']['username'])
                    except User.DoesNotExist:
                        user_obj = importing_user

                    action_obj = Action.objects.create(
                        config_name_event=config_event_obj,
                        action_type=action['action_type'],
                        object_type=action['object_type'],
                        created_at=action['created_at'],
                        detail=action['detail'],
                        user=user_obj
                    )

    # Create the Assembly Part
    assembly_part_obj = AssemblyPart.objects.create(
        assembly_revision=new_revision,
        part=part_obj,
        parent=parent,
        note=assembly_part_data['note'],
        order=assembly_part_data['order']
    )
    print(assembly_part_obj)
    # Add all Config data for the Assembly Part
    if assembly_part_data['assemblypart_configdefaultevents']:
        for config_event in assembly_part_data['assemblypart_configdefaultevents']:
            config_event_obj = ConfigDefaultEvent.objects.create(
                created_at=config_event['created_at'],
                updated_at=config_event['updated_at'],
                assembly_part=assembly_part_obj,
                approved=config_event['approved'],
                detail=config_event['detail'],
            )

            # get Users for draft/approval fields. Use importing User if no match
            for user in config_event['user_draft']:
                try:
                    user_obj = User.objects.get(username=user['username'])
                except User.DoesNotExist:
                    user_obj = importing_user
                # add to ManyToManyField
                config_event_obj.user_draft.add(user_obj)

            for user in config_event['user_approver']:
                try:
                    user_obj = User.objects.get(username=user['username'])
                except User.DoesNotExist:
                    user_obj = importing_user
                # add to ManyToManyField
                config_event_obj.user_approver.add(user_obj)

            for config_default in config_event['config_defaults']:
                # Get the matching local ConfigName object for this ConfigDefault
                config_name_obj = ConfigName.objects.filter(
                    name=config_default['config_name']['name'],
                    config_name_event__part=part_obj
                ).first()
                print(config_name_obj)
                # Create Config Default
                config_default_obj = ConfigDefault.objects.create(
                    conf_def_event=config_event_obj,
                    default_value=config_default['default_value'],
                    created_at=config_default['created_at'],
                    config_name=config_name_obj,
                )

            # add Action history for this event
            for action in config_event['actions']:
                # get User for Action. Use importing User if no match
                try:
                    user_obj = User.objects.get(username=action['user']['username'])
                except User.DoesNotExist:
                    user_obj = importing_user

                action_obj = Action.objects.create(
                    config_default_event=config_event_obj,
                    action_type=action['action_type'],
                    object_type=action['object_type'],
                    created_at=action['created_at'],
                    detail=action['detail'],
                    user=user_obj
                )
    # Loop through the tree
    for child_url in assembly_part_data['children']:
        _api_import_assembly_parts_tree(headers, child_url, new_revision, assembly_part_obj)

    return True


# View to make API request to a separate RDB instance and copy an Assembly Template
# url params: import_url = 'https://rdb-demo.whoi.edu/api/v1/assembly-templates/assemblies/8/'
#             api_token = string
class ImportAssemblyAPIRequestCopyView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'assemblies.add_assembly'

    def get(self, request, *args, **kwargs):
        import_url = request.GET.get('import_url')
        api_token = request.GET.get('api_token')
        assembly_revisions = request.GET.get('assembly_revisions')

        if not import_url:
            return HttpResponse("No import_url query paramater data")

        if not api_token:
            return HttpResponse("No api_token query paramater data")

        headers = {
            'Authorization': 'Token ' + api_token,
        }
        params = {'expand': 'assembly_type,assembly_revisions'}
        # Get the Assembly data from RDB API
        assembly_request = requests.get(import_url, params=params, headers=headers, verify=False)
        new_assembly = assembly_request.json()
        # Get or create new parent Temp Assembly
        assembly_obj, created = Assembly.objects.get_or_create(name=new_assembly['name'],
                                                               assembly_number=new_assembly['assembly_number'],
                                                               defaults={'description': new_assembly['description']},)
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
            if assembly_revisions:
                assembly_revisions_list = assembly_revisions.split(',')
                if rev['revision_code'] not in assembly_revisions_list:
                    continue

            assembly_revision_obj = AssemblyRevision.objects.create(
                revision_code=rev['revision_code'],
                revision_note=rev['revision_note'],
                created_at=rev['created_at'],
                assembly=assembly_obj,
            )
            print(assembly_revision_obj)

            for root_url in rev['assembly_parts_roots']:
                tree_created = _api_import_assembly_parts_tree(
                    headers, root_url, assembly_revision_obj, None, self.request.user)

            print(tree_created)
            # AssemblyPart._tree_manager.rebuild()
        return HttpResponse('<h1>New Assembly Template Imported! - %s</h1>' % (assembly_obj))


# import Gliders from rdb-demo
class ImportAllAssemblyTypeView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'assemblies.add_assembly'

    def get(self, request, *args, **kwargs):
        #import_url = "https://rdb-demo.whoi.edu/api/v1/assembly-templates/assembly-types/2/"
        import_url = request.GET.get('import_url')
        api_token = request.GET.get('api_token')
        mooring_id = request.GET.get('mooring_id')

        if not mooring_id:
            return HttpResponse("No mooring_id query paramater data")

        if not api_token:
            return HttpResponse("No api_token query paramater data")

        headers = {
            'Authorization': 'Token ' + api_token,
        }
        params = {"expand": "assemblies"}

        # Get the Assembly data from RDB API
        assembly_request = requests.get(
            import_url, params=params, headers=headers, verify=False
        )
        all_assemblies = assembly_request.json()
        assemblies = [assembly for assembly in all_assemblies["assemblies"] if mooring_id in assembly['name']]

        for assembly in assemblies:
            print(assembly["url"])
            import_url = assembly["url"]

            headers = {
                'Authorization': 'Token ' + api_token,
            }
            params = {'expand': 'assembly_type,assembly_revisions'}
            # Get the Assembly data from RDB API
            assembly_request = requests.get(import_url, params=params, headers=headers, verify=False)
            new_assembly = assembly_request.json()
            # Get or create new parent Temp Assembly
            assembly_obj, created = Assembly.objects.get_or_create(name=new_assembly['name'],
                                                                   assembly_number=new_assembly['assembly_number'],
                                                                   defaults={'description': new_assembly['description']},)
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
                    revision_code=rev['revision_code'],
                    revision_note=rev['revision_note'],
                    created_at=rev['created_at'],
                    assembly=assembly_obj,
                )
                print(assembly_revision_obj)

                for root_url in rev['assembly_parts_roots']:
                    tree_created = _api_import_assembly_parts_tree(
                        headers, root_url, assembly_revision_obj, None, self.request.user)

                print(tree_created)

        return HttpResponse('<h1>Gliders imported</h1>')


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
