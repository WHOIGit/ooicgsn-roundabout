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
import re
from decimal import Decimal
from types import SimpleNamespace
import itertools

from celery import shared_task
from dateutil import parser
from django.core.cache import cache
from django.db import transaction
from roundabout.ooi_ci_tools.forms import validate_reference_designator
from roundabout.parts.models import Part, PartType, Revision
from sigfig import round
from statistics import mean, stdev
from django.utils.timezone import make_aware

from roundabout.calibrations.forms import parse_coeff_1d_array
from roundabout.calibrations.models import CoefficientName, CoefficientValueSet, CalibrationEvent, CoefficientNameEvent, CoefficientValue
from roundabout.configs_constants.models import ConfigName, ConfigValue, ConfigEvent
from roundabout.cruises.models import Cruise, Vessel
from roundabout.inventory.models import Inventory, Action, Deployment, InventoryDeployment
from roundabout.inventory.utils import _create_action_history
from roundabout.userdefinedfields.models import Field, FieldValue
from roundabout.ooi_ci_tools.models import Threshold, ReferenceDesignator, ReferenceDesignatorEvent, BulkUploadEvent, BulkFile, BulkAssetRecord, BulkVocabRecord, CruiseEvent, VesselEvent
from roundabout.assemblies.models import Assembly, AssemblyPart, AssemblyRevision
from roundabout.locations.models import Location
from roundabout.builds.models import Build
from roundabout.core.utils import set_app_labels
from roundabout.assemblies.views import _make_revision_tree_copy

labels = set_app_labels()

import logging
logger = logging.getLogger(__name__)

# Update Coefficient statistical Threshold values for a Part's Calibration Names
@shared_task(bind = True, soft_time_limit = 3600)
def async_update_cal_thresholds(self):
    event = cache.get('thrsh_evnt')
    if event:
        cal_names = event.inventory.part.part_coefficientnameevents.first().coefficient_names.all()
    else:
        cal_names = CoefficientName.objects.all()
    for name in cal_names:
        if name.threshold_low and name.threshold_high:
            std_low = round(name.threshold_low, notation = 'std', output_type=float)
            std_high = round(name.threshold_high, notation = 'std', output_type=float)
            Threshold.objects.update_or_create(
                coefficient_name = name,
                defaults = {
                    'low': std_low,
                    'high': std_high
                }
            )
            continue
        if name.coefficient_value_sets.exists():
            valsets = name.coefficient_value_sets.all()
            std_vals = []
            for valset in valsets:
                vals = valset.coefficient_values.all()
                for val in vals:
                    std_val = round(val.original_value, notation = 'std', output_type=float)
                    std_vals.append(std_val)
            if len(std_vals) >= 2:
                name_avg = mean(std_vals)
                name_stdev = stdev(std_vals)
                Threshold.objects.update_or_create(
                    coefficient_name = name,
                    defaults = {
                        'low': name_avg - (name_stdev * 3),
                        'high': name_avg + (name_stdev * 3)
                    }
                )
            else:
                Threshold.objects.update_or_create(
                    coefficient_name = name,
                    defaults = {
                        'low': 0,
                        'high': 0
                    }
                )
        else:
            Threshold.objects.update_or_create(
                coefficient_name = name,
                defaults = {
                    'low': 0,
                    'high': 0
                }
            )
    cache.delete('thrsh_evnt')

# Parse Calibration CSV file submissions, generate and associate relevant Events
@shared_task(bind = True, soft_time_limit = 3600)
def parse_cal_files(self):
    self.update_state(state='PROGRESS', meta = {'key': 'started',})
    user = cache.get('user')
    user_draft = cache.get('user_draft')
    ext_files = cache.get('ext_files')
    csv_files = cache.get('csv_files')
    counter = 0
    for cal_csv in csv_files:
        counter += 1
        self.update_state(state='PROGRESS', meta = {'progress': counter, 'total': len(csv_files)})
        cal_csv_filename = cal_csv.name[:-4]
        cal_csv.seek(0)
        reader = csv.DictReader(io.StringIO(cal_csv.read().decode('utf-8')))
        headers = reader.fieldnames
        coeff_val_sets = []
        config_val_sets = []
        const_val_sets = []
        inv_serial = cal_csv.name.split('__')[0]
        cal_date_string = cal_csv.name.split('__')[1][:8]
        inventory_item = Inventory.objects.get(serial_number=inv_serial)
        cal_date_date = datetime.datetime.strptime(cal_date_string, "%Y%m%d").date()
        custom_field = Field.objects.get(field_name='Manufacturer Serial Number')
        try:
            inv_manufacturer_serial = FieldValue.objects.get(inventory=inventory_item,field=custom_field,is_current=True)
        except FieldValue.DoesNotExist:
            inv_manufacturer_serial = FieldValue.objects.create(inventory=inventory_item,field=custom_field,is_current=True)
        try:
            deployment = Deployment.objects.get(
                deployment_to_field_date__year=cal_date_date.year,
                deployment_to_field_date__month=cal_date_date.month,
                deployment_to_field_date__day=cal_date_date.day,
            )
        except Deployment.DoesNotExist:
            deployment = None
        conf_event, conf_created = ConfigEvent.objects.get_or_create(
            configuration_date = cal_date_date,
            inventory = inventory_item,
            config_type = 'conf',
            deployment = deployment
        )
        cnst_event, cnst_created = ConfigEvent.objects.get_or_create(
            configuration_date = cal_date_date,
            inventory = inventory_item,
            config_type = 'cnst',
            deployment = deployment
        )
        csv_event, cal_created = CalibrationEvent.objects.get_or_create(
            calibration_date = cal_date_date,
            inventory = inventory_item
        )
        for idx, row in enumerate(reader):
            row_data = row.items()
            for key, value in row_data:
                if key == 'serial':
                    csv_manufacturer_serial = value.strip()
                    if len(inv_manufacturer_serial.field_value) == 0 and len(csv_manufacturer_serial) > 0:
                        inv_manufacturer_serial.field_value = csv_manufacturer_serial
                        inv_manufacturer_serial.save()
                if key == 'name':
                    calibration_name = value.strip()
                    try:
                        cal_name_item = CoefficientName.objects.get(
                            calibration_name = calibration_name,
                            coeff_name_event = inventory_item.part.part_coefficientnameevents.first()
                        )
                    except CoefficientName.DoesNotExist:
                        cal_name_item = None
                    try:
                        config_name_item = ConfigName.objects.get(
                            name = calibration_name,
                            config_name_event = inventory_item.part.part_confignameevents.first()
                        )
                    except ConfigName.DoesNotExist:
                        config_name_item = None
                elif key == 'value':
                    valset_keys = {'cal_dec_places': inventory_item.part.cal_dec_places}
                    mock_valset_instance = SimpleNamespace(**valset_keys)
                    raw_valset = str(value)
                    value_set_type = 'sl'
                    if '[' in raw_valset:
                        raw_valset = raw_valset[1:-1]
                        value_set_type = '1d'
                    if 'SheetRef' in raw_valset:
                        ext_finder_filename = "__".join((cal_csv_filename,calibration_name))
                        ref_file = [file for file in ext_files if ext_finder_filename in file.name][0]
                        ref_file.seek(0)
                        reader = io.StringIO(ref_file.read().decode('utf-8'))
                        contents = reader.getvalue()
                        raw_valset = contents
                        value_set_type = '2d'
                elif key == 'notes':
                    notes = value.strip()
                    if cal_name_item:
                        coeff_val_set = {
                            'coefficient_name': cal_name_item,
                            'value_set': raw_valset,
                            'notes': notes
                        }
                        coeff_val_sets.append(coeff_val_set)
                    if config_name_item:
                        if config_name_item.config_type == 'conf':
                            config_val_set = {
                                'config_name': config_name_item,
                                'config_value': raw_valset,
                                'notes': notes,
                                'config_event': conf_event
                            }
                            config_val_sets.append(config_val_set)
                        if config_name_item.config_type == 'cnst':
                            const_val_set = {
                                'config_name': config_name_item,
                                'config_value': raw_valset,
                                'notes': notes,
                                'config_event': cnst_event
                            }
                            const_val_sets.append(const_val_set)
                    if not cal_name_item and not config_name_item:
                        if not inventory_item.part.part_coefficientnameevents.exists():
                            coeff_name_event = CoefficientNameEvent.objects.create(part = inventory_item.part)
                            _create_action_history(coeff_name_event, Action.CALCSVIMPORT, user, data=dict(csv_import=cal_csv.name))
                        else:
                            coeff_name_event = inventory_item.part.part_coefficientnameevents.first()
                        cal_name_item = CoefficientName.objects.create(
                            calibration_name = calibration_name,
                            coeff_name_event = coeff_name_event,
                            value_set_type = value_set_type
                        )
                        coeff_val_set = {
                            'coefficient_name': cal_name_item,
                            'value_set': raw_valset,
                            'notes': notes
                        }
                        coeff_val_sets.append(coeff_val_set)
        if user_draft.exists():
            for draft_user in user_draft:
                csv_event.user_draft.add(draft_user)
        if len(coeff_val_sets) >= 1:
            for valset in coeff_val_sets:
                valset['calibration_event'] = csv_event
                coeff_val_set, created = CoefficientValueSet.objects.update_or_create(
                    coefficient_name = valset['coefficient_name'],
                    calibration_event = valset['calibration_event'],
                    defaults = {
                        'value_set': valset['value_set'],
                        'notes': valset['notes'],
                    }
                )
                parse_coeff_vals(coeff_val_set)
            if cal_created:
                _create_action_history(csv_event, Action.CALCSVIMPORT, user, data=dict(csv_import=cal_csv.name))
            else:
                _create_action_history(csv_event, Action.CALCSVUPDATE, user, data=dict(csv_import=cal_csv.name))
        else:
            csv_event.delete()
        if len(config_val_sets) >= 1:
            for valset in config_val_sets:
                valset['config_event'] = conf_event
                coeff_val_set, created = ConfigValue.objects.update_or_create(
                    config_name = valset['config_name'],
                    config_event = valset['config_event'],
                    defaults = {
                        'config_value': valset['config_value'],
                        'notes': valset['notes'],
                    }
                )
            if conf_created:
                _create_action_history(conf_event, Action.CALCSVIMPORT, user, data=dict(csv_import=cal_csv.name))
            else:
                _create_action_history(conf_event, Action.CALCSVUPDATE, user, data=dict(csv_import=cal_csv.name))
        else:
            conf_event.delete()
        if len(const_val_sets) >= 1:
            for valset in const_val_sets:
                valset['config_event'] = cnst_event
                const_val_set, created = ConfigValue.objects.update_or_create(
                    config_name = valset['config_name'],
                    config_event = valset['config_event'],
                    defaults = {
                        'config_value': valset['config_value'],
                        'notes': valset['notes'],
                    }
                )
            if cnst_created:
                _create_action_history(cnst_event, Action.CALCSVIMPORT, user, data=dict(csv_import=cal_csv.name))
            else:
                _create_action_history(cnst_event, Action.CALCSVUPDATE, user, data=dict(csv_import=cal_csv.name))
        else:
            cnst_event.delete()
    async_update_cal_thresholds.delay()
    cache.delete('user_draft')
    cache.delete('ext_files')
    cache.delete('csv_files')

# Creates Coefficient value model instances for a valid CoefficientValueSet
def parse_coeff_vals(value_set_instance):
    set_type = value_set_instance.coefficient_name.value_set_type
    coeff_vals = CoefficientValue.objects.filter(coeff_value_set = value_set_instance)
    coeff_batch = []
    mega_batch = []
    if coeff_vals:
        coeff_vals.delete()
    if set_type  == 'sl' or set_type  == '1d':
        coeff_1d_array = value_set_instance.value_set.split(',')
        coeff_batch = parse_coeff_1d_array(coeff_1d_array, value_set_instance)
        mega_batch.extend(coeff_batch)
        # CoefficientValue.objects.bulk_create(coeff_batch)
    elif set_type == '2d':
        val_array = []
        coeff_2d_array = value_set_instance.value_set.splitlines()
        for val_set_index, val_set in enumerate(coeff_2d_array):
            coeff_1d_array = val_set.split(',')
            parsed_batch = parse_coeff_1d_array(coeff_1d_array, value_set_instance, val_set_index)
            val_array.extend(parsed_batch)
        mega_batch.extend(val_array)
        # CoefficientValue.objects.bulk_create(val_array)
    str_valset_id = str(value_set_instance.id)
    cache.set('coeff_vals_'+str_valset_id, mega_batch, timeout=None)
    bulk_upload_vals.delay(str_valset_id)
    return value_set_instance

@shared_task(bind=True, soft_time_limit = 3600)
def bulk_upload_vals(self, value_set_id):
    str_id = str(value_set_id)
    coeff_vals = cache.get('coeff_vals_'+str_id)
    CoefficientValue.objects.bulk_create(coeff_vals)
    cache.delete('coeff_vals_'+str_id)



# Parse Cruise CSV file submissions, generate and associate relevant Events
@shared_task(bind=True, soft_time_limit = 3600)
def parse_cruise_files(self):
    cruises_files = cache.get('cruises_files')
    user_draft = cache.get('user_draft_cruises')
    user = cache.get('user')
    for csv_file in cruises_files:
        # Set up the Django file object for CSV DictReader
        csv_file.seek(0)
        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
        # Get the column headers to save with parent TempImport object
        headers = reader.fieldnames
        # Set up data lists for returning results
        cruises_created = []
        cruises_updated = []
        
        for row in reader:
            cuid = row['CUID']
            cruise_start_date = parser.parse(row['cruiseStartDateTime'])
            cruise_stop_date = parser.parse(row['cruiseStopDateTime'])
            vessel_obj = None
            vessel_event = None
            # parse out the vessel name to match its formatting from Vessel CSV
            vessel_name_csv = row['ShipName'].strip()
            if vessel_name_csv == 'N/A':
                vessel_name_csv = None

            if vessel_name_csv:
                # update or create Cruise object based on CUID field
                try:
                    vessel_obj, vessel_created = Vessel.objects.get_or_create(
                        vessel_name = vessel_name_csv,
                    )
                except Vessel.MultipleObjectsReturned:
                    vessel_obj = Vessel.objects.filter(vessel_name=vessel_name_csv).first()
                if vessel_created:
                    _create_action_history(vessel_obj, Action.ADD, user, data=dict(csv_import=csv_file.name))

                vessel_event, event_created = VesselEvent.objects.update_or_create(vessel=vessel_obj)

                if event_created:
                    _create_action_history(vessel_event,Action.CALCSVIMPORT,user,data=dict(csv_import=csv_file.name))
                else:
                    _create_action_history(vessel_event,Action.CALCSVUPDATE,user,data=dict(csv_import=csv_file.name))

            # update or create Cruise object based on CUID field
            defaults = {'notes': row['notes'],
                        'cruise_start_date': cruise_start_date,
                        'cruise_stop_date': cruise_stop_date,
                        'vessel': vessel_obj,
                       }
            try:
                cruise_obj = Cruise.objects.get(CUID=cuid)
                orig_default = {key:str(getattr(cruise_obj,key,None)) for key in defaults}
            except (Cruise.DoesNotExist,Cruise.MultipleObjectsReturned): orig_default = None
            cruise_obj, created = Cruise.objects.update_or_create(
                CUID = cuid, defaults = defaults,
            )

            cruise_event, event_created = CruiseEvent.objects.update_or_create(cruise=cruise_obj)

            action_data = dict(updated_values=dict(), csv_import=csv_file.name)
            if created:
                cruises_created.append(cruise_obj)
                action_data["updated_values"]["CUID"] = {"from": None, "to": cuid}
                for field,new_val in defaults.items():
                    action_data["updated_values"][field] = {"from": None, "to": str(new_val)}
                _create_action_history(cruise_obj,Action.ADD,user,data=action_data)
            else:
                cruises_updated.append(cruise_obj)
                for field,new_val in defaults.items():
                    orig_val = orig_default[field] if orig_default else 'unknown'
                    if str(orig_val).rstrip('+00:00') != str(new_val).rstrip('+00:00'):
                        action_data["updated_values"][field] = {"from": str(orig_val).rstrip('+00:00'), "to": str(new_val).rstrip('+00:00')}
                _create_action_history(cruise_obj,Action.UPDATE,user,data=action_data)
            if user_draft.exists():
                cruise_event.user_draft.clear()
                cruise_event.user_approver.clear()
                if vessel_event:
                    vessel_event.user_draft.clear()
                    vessel_event.user_approver.clear()
                for draft_user in user_draft:
                    cruise_event.user_draft.add(draft_user)
                    if vessel_event:
                        vessel_event.user_draft.add(draft_user)
            if event_created:
                _create_action_history(cruise_event,Action.CALCSVIMPORT,user,data=dict(csv_import=csv_file.name))
            else:
                _create_action_history(cruise_event,Action.CALCSVUPDATE,user,data=dict(csv_import=csv_file.name))
    cache.delete("user_draft")
    cache.delete('cruises_files')



# Parse Vessel CSV file submissions, generate and associate relevant Events
@shared_task(bind=True, soft_time_limit = 3600)
def parse_vessel_files(self):
    vessels_files = cache.get('vessels_files')
    user_draft = cache.get('user_draft_vessels')
    user = cache.get('user')
    for csv_file in vessels_files:
        # Set up the Django file object for CSV DictReader
        csv_file.seek(0)
        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
        # Get the column headers to save with parent TempImport object
        headers = reader.fieldnames
        # Set up data lists for returning results
        vessels_created = []
        vessels_updated = []
        for row in reader:
            vessel_name = row['Vessel Name'].strip()
            MMSI_number = None
            IMO_number = None
            length = None
            max_speed = None
            max_draft = None
            active = re.sub(r'[()]', '', row['Active'])
            R2R = row['R2R']

            if row['MMSI#']:
                MMSI_number = int(re.sub('[^0-9]','', row['MMSI#']))

            if row['IMO#']:
                IMO_number = int(re.sub('[^0-9]','', row['IMO#']))

            if row['Length (m)']:
                length = Decimal(row['Length (m)'])

            if row['Max Speed (m/s)']:
                max_speed = Decimal(row['Max Speed (m/s)'])

            if row['Max Draft (m)']:
                max_draft = Decimal(row['Max Draft (m)'])

            if active:
                if active == 'Y':
                    active = True
                else:
                    active = False
            if R2R:
                if R2R == 'Y':
                    R2R = True
                else:
                    R2R = False

            # update or create Vessel object based on vessel_name field
            defaults = {
                'prefix': row['Prefix'],
                'vessel_designation': row['Vessel Designation'],
                'ICES_code': row['ICES Code'],
                'operator': row['Operator'],
                'call_sign': row['Call Sign'],
                'MMSI_number': MMSI_number,
                'IMO_number': IMO_number,
                'length': length,
                'max_speed': max_speed,
                'max_draft': max_draft,
                'designation': row['Designation'],
                'active': active,
                'R2R': R2R,
            }
            try:
                vessel_obj, created = Vessel.objects.update_or_create(
                    vessel_name = vessel_name, defaults=defaults,
                )
            except (Vessel.MultipleObjectsReturned):
                 vessel_obj = Vessel.objects.filter(vessel_name = vessel_name).first()
                 created = False
            
            if not created:
                orig_default = {key:str(getattr(vessel_obj,key,None)) for key in defaults}
            else:
                orig_default = None

            vessel_event, event_created = VesselEvent.objects.update_or_create(vessel=vessel_obj)

            action_data = dict(updated_values=dict(), csv_import=csv_file.name)
            if created:
                vessels_created.append(vessel_obj)
                action_data["updated_values"]["vessel_name"] = {"from": None, "to": vessel_name}
                for field,new_val in defaults.items():
                    action_data["updated_values"][field] = {"from": None, "to": str(new_val)}
                _create_action_history(vessel_obj,Action.ADD,user,data=action_data)
            else:
                vessels_updated.append(vessel_obj)
                for field,new_val in defaults.items():
                    orig_val = orig_default[field] if orig_default else 'unknown'
                    if str(orig_val).rstrip('.0') != str(new_val).rstrip('.0'):
                        action_data["updated_values"][field] = {"from": str(orig_val).rstrip('.0'), "to": str(new_val).rstrip('.0')}
                _create_action_history(vessel_obj,Action.UPDATE,user,data=action_data)
            if user_draft.exists():
                vessel_event.user_draft.clear()
                vessel_event.user_approver.clear()
                for draft_user in user_draft:
                    vessel_event.user_draft.add(draft_user)
            if event_created:
                _create_action_history(vessel_event,Action.CALCSVIMPORT,user,data=dict(csv_import=csv_file.name))
            else:
                _create_action_history(vessel_event,Action.CALCSVUPDATE,user,data=dict(csv_import=csv_file.name))
    cache.delete('vessels_files')


# Parse Deployment CSV file submissions, generate and associate relevant Events
@shared_task(bind=True, soft_time_limit = 3600)
def parse_deployment_files(self):
    csv_files = cache.get('dep_files')
    user_draft = cache.get('user_draft_deploy')
    user = cache.get('user')
    # Set up the Django file object for CSV DictReader
    for csv_file in csv_files:
        csv_file.seek(0)
        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
        headers = reader.fieldnames
        # Restructure CSV data to group rows by Deployment
        deployment_imports = []
        for row in reader:
            if '#' not in row['CUID_Deploy']:
                if not any(dict['mooring.uid'] == row['mooring.uid'] for dict in deployment_imports):
                    # get Assembly number from RefDes as that seems to be most consistent across CSVs
                    ref_des = row['Reference Designator']
                    assembly = ref_des.split('-')[0]
                    if 'MOAS' in ref_des:
                        extended_ref_des = ref_des.split('-')[1]
                        assembly = f'{assembly}-{extended_ref_des}'
                    
                    dep_number_string = row['mooring.uid'].split('-')[2]
                    # parse together the Build/Deployment Numbers from CSV fields
                    deployment_number = f'{assembly}-{dep_number_string}'
                    build_number = f'Historical {dep_number_string}'
                    assembly_template_revision = 'A'
                    if 'assembly_template_revision' in row.keys():
                        if row['assembly_template_revision'] != '':
                            assembly_template_revision = row['assembly_template_revision']
                    # build data dict
                    mooring_uid_dict = {
                        'mooring.uid': row['mooring.uid'],
                        'assembly': assembly,
                        'build_number': build_number,
                        'deployment_number': deployment_number,
                        'assembly_template_revision': assembly_template_revision,
                        'rows': [],
                    }
                    deployment_imports.append(mooring_uid_dict)

                deployment = next((deployment for deployment in deployment_imports if deployment['mooring.uid'] == row['mooring.uid']), False)
                deployment['rows'].append(row)
        # loop through the Deployments
        for deployment_import in deployment_imports:
            # get the Assembly template for this Build, needs to be only one match
            try:
                assembly = Assembly.objects.get(assembly_number=deployment_import['assembly'])
            except Assembly.DoesNotExist:
                raise ValueError("no assembly found")
            except Assembly.MultipleObjectsReturned:
                raise ValueError("too many assemblies found")
            
            assembly_revision_created = False

            deployment_import_revision = deployment_import['assembly_template_revision'] 
            try:
                assembly_revision, assembly_revision_created = AssemblyRevision.objects.get_or_create(assembly=assembly, revision_code=deployment_import_revision)
            except AssemblyRevision.MultipleObjectsReturned:
                assembly_revision = AssemblyRevision.objects.filter(assembly=assembly, revision_code=deployment_import_revision).latest()

            if assembly_revision_created:
                assm_revs = assembly.assembly_revisions.exclude(revision_code=deployment_import_revision)
                if len(assm_revs):
                    latest_revision = assm_revs.latest()
                    for assembly_part in latest_revision.assembly_parts.all():
                        
                        if assembly_part.is_root_node():
                            _make_revision_tree_copy(
                                assembly_part,
                                assembly_revision,
                                assembly_part.parent,
                                user,
                                False,
                            )
            assembly_revision.save()

            # set up common variables for Builds/Deployments
            location_code = deployment_import['assembly'][0:2]

            try:
                deployed_location = Location.objects.get(location_code=location_code)
            except Location.DoesNotExist:
                raise ValueError("No Location Matching this Location Code")

            dep_start_date = make_aware(parser.parse(deployment_import['rows'][0]['startDateTime']))

            try:
                dep_end_date = make_aware(parser.parse(deployment_import['rows'][0]['stopDateTime']))
            except:
                dep_end_date = None

            try:
                cruise_deployed = Cruise.objects.get(CUID=deployment_import['rows'][0]['CUID_Deploy'])
            except:
                cruise_deployed = None

            try:
                cruise_recovered = Cruise.objects.get(CUID=deployment_import['rows'][0]['CUID_Recover'])
            except:
                cruise_recovered = None

            # Set Build location dependiing on Deployment status
            if dep_end_date:
                build_location, created = Location.objects.get_or_create(name='Retired')
                if created:
                    build_location.root_type = 'Retired'
                    build_location.weight = 500
                    build_location.save()
            else:
                build_location = deployed_location

            latitude = deployment_import['rows'][0]['lat']
            longitude = deployment_import['rows'][0]['lon']
            water_depth = deployment_import['rows'][0]['water_depth']

            # Get/Create a Build for this Deployment
            build, build_created = Build.objects.update_or_create(
                build_number=deployment_import['build_number'],
                assembly=assembly,
                defaults={
                    'assembly_revision': assembly_revision,
                    'created_at': dep_start_date,
                    'location': build_location,
                },
            )

            # Call the function to create an initial Action history
            if build_created:
                action = Action.objects.create(
                    action_type = Action.ADD,
                    object_type = Action.BUILD,
                    created_at = dep_start_date,
                    build = build,
                    location = deployed_location,
                    user = user,
                    detail = f'{Action.BUILD} first added to RDB',
                )

            # Update/Create Deployment for this Build
            try:
                deployment_obj, deployment_created = Deployment.objects.update_or_create(
                    deployment_number=deployment_import['deployment_number'],
                    build=build,
                    defaults={
                        'deployment_start_date': dep_start_date,
                        'deployment_burnin_date': dep_start_date,
                        'deployment_to_field_date': dep_start_date,
                        'deployment_recovery_date': dep_end_date,
                        'deployment_retire_date': dep_end_date,
                        'deployed_location': deployed_location,
                        'cruise_deployed': cruise_deployed,
                        'cruise_recovered': cruise_recovered,
                        'latitude': latitude,
                        'longitude': longitude,
                        'depth': float(water_depth),
                    },
                )
            except Deployment.MultipleObjectsReturned:
                print('ERROR', deployment_import['deployment_number'])

            # If this an update to existing Deployment, need to delete all previous Deployment History Actions
            if not deployment_created:
                deployment_actions = deployment_obj.actions.all()
                deployment_actions.delete()
            if user_draft.exists():
                deployment_obj.user_approver.clear()
                deployment_obj.user_draft.clear()
                for draft_user in user_draft:
                    deployment_obj.user_draft.add(draft_user)

            # _create_action_history function won't work correctly for back-dated Build Deployments,
            # need to add history Actions manually
            build_deployment_actions = [
                Action.STARTDEPLOYMENT,
                Action.DEPLOYMENTBURNIN,
                Action.DEPLOYMENTTOFIELD,
                Action.DEPLOYMENTRECOVER,
                Action.DEPLOYMENTRETIRE,
            ]

            for action in build_deployment_actions:
                create_action = False
                if action == Action.STARTDEPLOYMENT:
                    create_action = True
                    action_date = dep_start_date
                    detail = '%s %s started.' % (labels['label_deployments_app_singular'], deployment_obj)

                elif action == Action.DEPLOYMENTBURNIN:
                    create_action = True
                    action_date = dep_start_date
                    detail = '%s %s burn in.' % (labels['label_deployments_app_singular'], deployment_obj)

                elif action == Action.DEPLOYMENTTOFIELD:
                    create_action = True
                    action_date = dep_start_date
                    detail = 'Deployed to field on %s. Cruise: %s' % (deployment_obj, cruise_deployed)

                elif action == Action.DEPLOYMENTRECOVER and dep_end_date:
                    create_action = True
                    action_date = dep_end_date
                    detail = 'Recovered from %s. Cruise: %s' % (deployment_obj, cruise_recovered)

                elif action == Action.DEPLOYMENTRETIRE and dep_end_date:
                    create_action = True
                    action_date = dep_end_date
                    detail = '%s %s ended for this %s.' % (labels['label_deployments_app_singular'], deployment_obj, labels['label_inventory_app_singular'])

                if create_action:
                    action = Action.objects.create(
                        action_type = action,
                        object_type = Action.BUILD,
                        created_at = action_date,
                        build = build,
                        location = deployed_location,
                        deployment = deployment_obj,
                        deployment_type = Action.BUILD_DEPLOYMENT,
                        user = user,
                        detail = detail,
                    )

            for row in deployment_import['rows']:
                # create InventoryDeployments for each item
                if row['sensor.uid'] == '' and row['electrical.uid'] == '':
                    continue
                else:
                    if row['sensor.uid'] != '':
                        uid = row['sensor.uid']
                    elif row['electrical.uid'] != '':
                        uid = row['electrical.uid']
                    
                    # Find the AssemblyPart that matches this RefDes by searching the ConfigDefault values
                    # If no match, throw error.
                    try:
                        ref_des = row['Reference Designator']
                        ref_des_obj = ReferenceDesignator.objects.get(refdes_name=ref_des)
                    except ReferenceDesignator.MultipleObjectsReturned:
                        ref_des_obj = ReferenceDesignator.objects.filter(refdes_name=ref_des).first()
                    except ReferenceDesignator.DoesNotExist:
                        continue
                    except Exception as e:
                        print(e)
                        continue

                    assembly_part = ref_des_obj.assembly_parts.filter(part__isnull=False).first()

                    # Get/Update Inventory item with matching serial_number

                    try:
                        item = Inventory.objects.get(serial_number=uid)
                    except Inventory.DoesNotExist:
                        continue
                    

                    if item.assembly_part == None:
                        order = item.part.name
                        if item.part.friendly_name != '':
                            order = item.part.friendly_name
                        try:
                            assembly_part, assm_created = AssemblyPart.objects.update_or_create(
                                part = item.part,
                                assembly_revision=assembly_revision,
                                order=order,
                                defaults={
                                    'ci_deployedBy': row['deployedBy'],
                                    'ci_recoveredBy': row['recoveredBy'],
                                    'ci_versionNumber': row['versionNumber'],
                                    'ci_orbit': row['orbit'],
                                    'ci_deployment_depth': row['deployment_depth'],
                                    'ci_notes': row['notes'],
                                    'ci_electrical_uid': row['electrical.uid'],
                                    'ci_mooring_uid': row['mooring.uid'],
                                    'ci_node_uid': row['node.uid'],

                                }
                            )
                        except AssemblyPart.MultipleObjectsReturned:
                            assembly_part = AssemblyPart.objects.filter(part = item.part,assembly_revision=assembly_revision,order=order).first()
                        if assembly_part:
                            assembly_part.reference_designator = ref_des_obj
                            assembly_part.assembly = assembly
                            assembly_part.save()
                        item.assembly_part = assembly_part
                        item.save()
                    try:
                        refdes_event = ref_des_obj.assembly_part.assemblypart_referencedesignatorevents.first()
                    except Exception as e:
                        refdes_event = ReferenceDesignatorEvent.objects.create(
                            reference_designator = ref_des_obj,
                            assembly_part = item.assembly_part
                        )
                    refdes_event.assembly_part = item.assembly_part
                    refdes_event.save()
                    item.location = build_location
                    item.build = build
                    item.save()

                    # Get/Create Deployment for this Build
                    inv_deployment_obj, inv_deployment_created = InventoryDeployment.objects.update_or_create(
                        inventory=item,
                        deployment=deployment_obj,
                        defaults={
                            'assembly_part': assembly_part,
                            'deployment_start_date': dep_start_date,
                            'deployment_burnin_date': dep_start_date,
                            'deployment_to_field_date': dep_start_date,
                            'deployment_recovery_date': dep_end_date,
                            'deployment_retire_date': dep_end_date,
                            'cruise_deployed': cruise_deployed,
                            'cruise_recovered': cruise_recovered,
                        },
                    )

                    # Create/update Configuration values for this Deployment
                    config_event, config_event_created = ConfigEvent.objects.update_or_create(
                        inventory=item,
                        deployment=deployment_obj,
                        defaults={
                            'created_at': dep_start_date,
                            'configuration_date': dep_start_date,
                            'approved': True,
                            'config_type': 'conf',
                        },
                    )
                    config_event.user_approver.add(user)

                    config_name = ConfigName.objects.filter(name='Nominal Depth', part=item.part).first()

                    config_value, config_value_created = ConfigValue.objects.update_or_create(
                        config_event=config_event,
                        config_name=config_name,
                        defaults={
                            'config_value': row['deployment_depth'],
                            'created_at': dep_start_date,
                        },
                    )
                    _create_action_history(config_event, Action.CALCSVIMPORT, user)

                    # _create_action_history function won't work correctly fo Inventory Deployments if item is already in RDB,
                    # need to add history Actions manually

                    # create Build object action
                    action = Action.objects.create(
                        action_type = Action.SUBCHANGE,
                        object_type = Action.BUILD,
                        created_at = dep_start_date,
                        build = build,
                        location = deployed_location,
                        deployment = deployment_obj,
                        user = user,
                        detail = f'Sub-Assembly {item} added.',
                    )

                    # create Inventory object actions
                    inv_actions = [
                        Action.ADDTOBUILD,
                        Action.REMOVEFROMBUILD,
                    ]

                    inv_deployment_actions = [
                        Action.STARTDEPLOYMENT,
                        Action.DEPLOYMENTBURNIN,
                        Action.DEPLOYMENTTOFIELD,
                        Action.DEPLOYMENTRECOVER,
                        Action.DEPLOYMENTRETIRE,
                    ]

                    for action in inv_actions:
                        create_action = False

                        if action == Action.ADDTOBUILD:
                            create_action = True
                            action_date = dep_start_date
                            detail = 'Moved to %s.' % (build)

                        elif action == Action.REMOVEFROMBUILD and dep_end_date:
                            create_action = True
                            action_date = dep_end_date
                            detail = 'Removed from %s.' % (build)
                            # create Build object action
                            action = Action.objects.create(
                                action_type = Action.SUBCHANGE,
                                object_type = Action.BUILD,
                                created_at = action_date,
                                build = build,
                                location = deployed_location,
                                deployment = deployment_obj,
                                user = user,
                                detail = f'Sub-Assembly {item} removed.',
                            )

                        if create_action:
                            action = Action.objects.create(
                                action_type = action,
                                object_type = Action.INVENTORY,
                                created_at = action_date,
                                inventory = item,
                                build = build,
                                location = deployed_location,
                                deployment = deployment_obj,
                                user = user,
                                detail = detail,
                            )

                    for action in inv_deployment_actions:
                        create_action = False

                        if action == Action.STARTDEPLOYMENT:
                            create_action = True
                            action_date = dep_start_date
                            detail = '%s %s started.' % (labels['label_deployments_app_singular'], deployment_obj)

                        elif action == Action.DEPLOYMENTBURNIN:
                            create_action = True
                            action_date = dep_start_date
                            detail = '%s %s burn in.' % (labels['label_deployments_app_singular'], deployment_obj)

                        elif action == Action.DEPLOYMENTTOFIELD:
                            create_action = True
                            action_date = dep_start_date
                            detail = 'Deployed to field on %s.' % (deployment_obj)

                        elif action == Action.DEPLOYMENTRECOVER and dep_end_date:
                            create_action = True
                            action_date = dep_end_date
                            detail = 'Recovered from %s.' % (deployment_obj)

                        elif action == Action.DEPLOYMENTRETIRE and dep_end_date:
                            create_action = True
                            action_date = dep_end_date
                            detail = '%s %s ended for this %s.' % (labels['label_deployments_app_singular'], deployment_obj, labels['label_inventory_app_singular'])

                        if create_action:
                            action = Action.objects.create(
                                action_type = action,
                                object_type = Action.INVENTORY,
                                created_at = action_date,
                                inventory = item,
                                build = build,
                                location = deployed_location,
                                deployment = deployment_obj,
                                inventory_deployment = inv_deployment_obj,
                                deployment_type = Action.INVENTORY_DEPLOYMENT,
                                user = user,
                                detail = detail,
                            )
                    #print(row['sensor.uid'])
                    # get the latest Action for this item, if it's NOT later than action_date,
                    # need to update Item build/location date to match this Deployment
                    last_action = item.actions.latest()
                    if action_date >= last_action.created_at:
                        # remove from Build if Deployment is retired
                        if dep_end_date:
                            item.build = None
                            item.assembly_part = None
                        else:
                            item.build = build
                            item.assembly_part = assembly_part
                        item.location = build.location
                        item.save()
    cache.delete('dep_files')
    cache.delete('user_draft_deploy')


# Parse Reference Designator vocab CSV file submission, generate and associate relevant Events
@shared_task(bind=True, soft_time_limit = 3600)
def parse_refdes_files(self):
    refdes_files = cache.get('refdes_files')
    user = cache.get('user')
    user_draft = cache.get('user_draft_refdes')
    for csv_file in refdes_files:
        # Set up the Django file object for CSV DictReader
        csv_file.seek(0)
        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
        # Get the column headers to save with parent TempImport object
        headers = reader.fieldnames

        for row in reader:
            refdes_name = row['Reference_Designator']
            try:
                assertion_sets = refdes_name.split('-')
                assert len(assertion_sets) == 4
            except:
                continue
            try:
                refdes_valid = validate_reference_designator(refdes_name)
            except:
                continue
            try:
                min_depth = Decimal(row['Min Depth'])
            except:
                min_depth = 0
            try:
                max_depth = Decimal(row['Max Depth'])
            except:
                max_depth = 0
            try:
                refdes_obj, created = ReferenceDesignator.objects.update_or_create(
                    refdes_name = refdes_name,
                    defaults = {
                        'toc_l1': row['TOC_L1'],
                        'toc_l2': row['TOC_L2'],
                        'toc_l3': row['TOC_L3'],
                        'instrument': row['Instrument'],
                        'manufacturer': row['Manufacturer'],
                        'model': row['Model'],
                        'min_depth': min_depth,
                        'max_depth': max_depth
                    }
                )
            except ReferenceDesignator.MultipleObjectsReturned:
                refdes_obj = ReferenceDesignator.objects.filter(refdes_name=refdes_name).first()
                refdes_obj.toc_l1 = row['TOC_L1']
                refdes_obj.toc_l2 = row['TOC_L2']
                refdes_obj.toc_l3 = row['TOC_L3']
                refdes_obj.instrument = row['Instrument']
                refdes_obj.manufacturer = row['Manufacturer']
                refdes_obj.model = row['Model']
                refdes_obj.min_depth = min_depth
                refdes_obj.max_depth = max_depth
                refdes_obj.save()
            if created:
                refdes_event = ReferenceDesignatorEvent.objects.create()
                refdes_event.reference_designator = refdes_obj
                if user_draft.exists():
                    for draft_user in user_draft:
                        refdes_event.user_draft.add(draft_user)
                refdes_event.save()
                refdes_obj.save()
                _create_action_history(refdes_event,Action.ADD,user,data=dict(csv_import=csv_file.name))
            else:
                if refdes_obj.assembly_parts:
                    for assm in refdes_obj.assembly_parts.all():
                        for event in assm.assemblypart_referencedesignatorevents.all():
                            event.reference_designator = refdes_obj
                            if user_draft.exists():
                                event.user_approver.clear()
                                event.user_draft.clear()
                                for draft_user in user_draft:
                                    event.user_draft.add(draft_user)
                            event.save()

                            _create_action_history(event,Action.UPDATE,user,data=dict(csv_import=csv_file.name))
    cache.delete('refdes_files')
    cache.delete('user_draft_refdes')




# Parse Bulk Upload CSV file submissions 
# Generate and associate relevant Events, containing AssetRecords and Vocab objects
@shared_task(bind=True, soft_time_limit = 3600)
def parse_bulk_files(self):
    bulk_files = cache.get('bulk_files')
    user = cache.get('user')
    user_draft = cache.get('user_draft_bulk')
    bulk_event, event_created = BulkUploadEvent.objects.update_or_create(id=1)
    cache.set('bulk_event', bulk_event, timeout=None)  
    if user_draft.exists():
        bulk_event.user_draft.clear()
        bulk_event.user_approver.clear()
        for draft_user in user_draft:
            bulk_event.user_draft.add(draft_user)
    if event_created:
        _create_action_history(bulk_event,Action.CALCSVIMPORT,user)
    else:
        _create_action_history(bulk_event,Action.CALCSVUPDATE,user)
    counter = 0
    for csv_file in bulk_files:
        str_counter = str(counter)
        cache.set('csv_file_'+str_counter, csv_file, timeout=None)
        parse_bulk_file.delay(str_counter)
        counter += 1
    cache.delete('bulk_files')
    cache.delete('user_draft_bulk')

# Parse Bulk Upload CSV file submission as a separate task
@shared_task(bind=True, soft_time_limit = 3600)
def parse_bulk_file(self, counter):
    str_counter = str(counter)
    csv_file = cache.get('csv_file_'+str_counter)
    bulk_event = cache.get('bulk_event')
    user = cache.get('user')

    # Set up the Django file object for CSV DictReader
    csv_file.seek(0)
    reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))

    # Get the column headers to save with parent TempImport object
    headers = reader.fieldnames
    file_name = csv_file.name
    bulk_file, file_created = BulkFile.objects.update_or_create(file_name=file_name, bulk_upload_event=bulk_event)

    if csv_file.name.endswith('AssetRecord.csv'):
        for row in reader:
            try:
                asset_uid = row['ASSET_UID']
            except:
                continue
            assetrecord_obj, asset_created = BulkAssetRecord.objects.update_or_create(
                asset_uid = asset_uid,
                bulk_file = bulk_file,
                bulk_upload_event = bulk_event,
                defaults = {
                    'legacy_asset_uid': row['LEGACY_ASSET_UID'],
                    'asset_type': row['TYPE'],
                    'mobile': row['Mobile'],
                    'equip_desc': row['DESCRIPTION OF EQUIPMENT'],
                    'mio_inv_desc': row['MIO_Inventory_Description'],
                    'manufacturer': row['Manufacturer'],
                    'asset_model': row['Model'],
                    'manufacturer_serial_number': row["Manufacturer's Serial No./Other Identifier"],
                    'firmware_version': row['Firmware Version'],
                    'acquisition_date': row['ACQUISITION DATE'],
                    'original_cost': row['ORIGINAL COST'],
                    'comments': row['comments'],
                    'array_geometry': row['Array_geometry'] if hasattr(row,'Array_geometry') else '',
                    'commission_date': row['Commission_Date'] if hasattr(row,'Commission_Date') else '',
                    'decommission_date': row['Decommission_Date'] if hasattr(row,'Decommission_Date') else '',
                    'mio': row['MIO'] if hasattr(row,'MIO') else '',
                }
            )
            try:
                part_template = row['RDB_Part_Template']
            except:
                part_template = None
            inv = Inventory.objects.filter(serial_number = asset_uid)
            if inv:
                inv = inv.first()
                inv.bulk_upload_event = bulk_event
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI TYPE')[0],
                    is_current = True,
                    inventory = inv,
                    defaults={
                        'field_value': row['TYPE'],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI Mobile')[0],
                    is_current = True,
                    inventory = inv,
                    defaults = {
                        'field_value': row['Mobile'],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='Manufacturer Serial Number')[0],
                    is_current = True,
                    inventory = inv,
                    defaults= {
                        'field_value': row["Manufacturer's Serial No./Other Identifier"],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='Firmware Version')[0],
                    is_current = True,
                    inventory = inv,
                    defaults = {
                        'field_value': row['Firmware Version'],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='Date Received')[0],
                    is_current = True,
                    inventory = inv,
                    defaults = {
                        'field_value': row['ACQUISITION DATE'],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI comments')[0],
                    is_current = True,
                    inventory = inv,
                    defaults = {
                        'field_value': row['comments'],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='Owner')[0],
                    is_current = True,
                    inventory = inv,
                    defaults= {
                        'field_value': row['MIO'] if hasattr(row,'MIO') else '',
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI Array Geometry')[0],
                    is_current = True,
                    inventory = inv,
                    defaults= {
                        'field_value': row['Array_geometry'] if hasattr(row,'Array_geometry') else '',
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI Commission Date')[0],
                    is_current = True,
                    inventory = inv,
                    defaults= {
                        'field_value': row['Commission_Date'] if hasattr(row,'Commission_Date') else '',
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI Decommission Date')[0],
                    is_current = True,
                    inventory = inv,
                    defaults= {
                        'field_value': row['Decommission_Date'] if hasattr(row,'Decommission_Date') else '',
                    }
                )   
                inv.save()
                _create_action_history(inv,Action.CALCSVUPDATE,user,data=dict(csv_import=csv_file.name))
            if not inv and part_template is not None and part_template != '':
                inst_obj = PartType.objects.get(name='Instrument')

                #  Search Parts by Part Number across all Part Types
                all_type_search = PartType.objects.all()
                try:
                    part = Part.objects.get(
                        part_type__in=all_type_search, 
                        part_number=part_template
                    )
                except Part.MultipleObjectsReturned:
                    part = Part.objects.filter(
                        part_type__in=all_type_search, 
                        part_number=part_template
                    ).first()
                except Part.DoesNotExist:
                    part = Part.objects.create(name=part_template, part_type=inst_obj, part_number=part_template, bulk_upload_event=bulk_event)
                    rev_a = Revision.objects.create(part=part)
                inv, inv_created = Inventory.objects.get_or_create(
                    part = part,
                    serial_number = asset_uid,
                    bulk_upload_event = bulk_event,
                    location = Location.objects.get(name='Retired')
                )
                inv.save()
                if inv_created:
                    _create_action_history(inv,Action.CALCSVIMPORT,user,data=dict(csv_import=csv_file.name))
                        
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI TYPE')[0],
                    is_current = True,
                    inventory = inv,
                    defaults={
                        'field_value': row['TYPE'],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI Mobile')[0],
                    is_current = True,
                    inventory = inv,
                    defaults = {
                        'field_value': row['Mobile'],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='Manufacturer Serial Number')[0],
                    is_current = True,
                    inventory = inv,
                    defaults= {
                        'field_value': row["Manufacturer's Serial No./Other Identifier"],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='Firmware Version')[0],
                    is_current = True,
                    inventory = inv,
                    defaults = {
                        'field_value': row['Firmware Version'],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='Date Received')[0],
                    is_current = True,
                    inventory = inv,
                    defaults = {
                        'field_value': row['ACQUISITION DATE'],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI comments')[0],
                    is_current = True,
                    inventory = inv,
                    defaults = {
                        'field_value': row['comments'],
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='Owner')[0],
                    is_current = True,
                    inventory = inv,
                    defaults= {
                        'field_value': row['MIO'] if hasattr(row,'MIO') else '',
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI Array Geometry')[0],
                    is_current = True,
                    inventory = inv,
                    defaults= {
                        'field_value': row['Array_geometry'] if hasattr(row,'Array_geometry') else '',
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI Commission Date')[0],
                    is_current = True,
                    inventory = inv,
                    defaults= {
                        'field_value': row['Commission_Date'] if hasattr(row,'Commission_Date') else '',
                    }
                )
                FieldValue.objects.update_or_create(
                    field = Field.objects.get_or_create(field_name='CI Decommission Date')[0],
                    is_current = True,
                    inventory = inv,
                    defaults= {
                        'field_value': row['Decommission_Date'] if hasattr(row,'Decommission_Date') else '',
                    }
                )
    if csv_file.name.endswith('vocab.csv'):
        for row in reader:
            manufacturer = None
            asset_model = None
            equip_desc = row['DESCRIPTION OF EQUIPMENT']
            if 'manufacturer' in row:
                manufacturer = row['manufacturer'].strip()
            if 'Manufacturer' in row:
                manufacturer = row['Manufacturer'].strip()
            if 'model' in row:
                asset_model = row['model'].strip()
            if 'Model' in row:
                asset_model = row['Model'].strip()
            vocabrecord_obj, vocab_created = BulkVocabRecord.objects.update_or_create(
                equip_desc = equip_desc,
                bulk_file = bulk_file,
                bulk_upload_event = bulk_event,
                defaults = {
                    'manufacturer': manufacturer,
                    'asset_model': asset_model,
                }
            )
            man_field_list = FieldValue.objects.filter(field__field_name__icontains='Manufacturer', field_value__icontains = manufacturer, part__isnull=False, is_current=True)
            mod_field_list = FieldValue.objects.filter(field__field_name__icontains='Model', field_value__icontains = asset_model, part__isnull=False, is_current=True)
            if len(man_field_list) and len(mod_field_list):
                for (man_field_obj, mod_field_obj) in zip(man_field_list, mod_field_list):
                    if man_field_obj.part == mod_field_obj.part:
                        field_part = man_field_obj.part
                        field_part.bulk_upload_event = bulk_event
                        field_part.save()
    cache.delete('csv_file_'+str_counter)