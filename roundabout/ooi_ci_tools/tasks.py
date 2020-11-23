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


import datetime
from types import SimpleNamespace

import csv
import io
import re
from decimal import Decimal

from dateutil import parser
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView, FormView

from celery import shared_task

from roundabout.calibrations.forms import parse_valid_coeff_vals
from roundabout.calibrations.models import CoefficientName, CoefficientValueSet, CalibrationEvent
from roundabout.configs_constants.models import ConfigName, ConfigValue, ConfigEvent
from roundabout.cruises.models import Cruise, Vessel
from roundabout.inventory.models import Inventory, Action, Deployment
from roundabout.inventory.utils import _create_action_history


@shared_task(bind = True)
def parse_cal_files(self):
    self.update_state(state='PROGRESS', meta = {'key': 'started',})
    user = cache.get('user')
    user_draft = cache.get('user_draft')
    ext_files = cache.get('ext_files')
    csv_files = cache.get('csv_files')
    counter = 0
    for cal_csv in csv_files:
        counter+=1
        self.update_state(state='PROGRESS', meta = {'progress': counter, 'total': len(cal_csv)})
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
        try:
            deployment = Deployment.objects.get(
                deployment_to_field_date__year=cal_date_date.year,
                deployment_to_field_date__month=cal_date_date.month,
                deployment_to_field_date__day=cal_date_date.day,
            )
        except Deployment.DoesNotExist:
            deployment = None
        conf_event, created = ConfigEvent.objects.get_or_create(
            configuration_date = cal_date_date,
            inventory = inventory_item,
            config_type = 'conf',
            deployment = deployment
        )
        cnst_event, created = ConfigEvent.objects.get_or_create(
            configuration_date = cal_date_date,
            inventory = inventory_item,
            config_type = 'cnst',
            deployment = deployment
        )
        csv_event, created = CalibrationEvent.objects.get_or_create(
            calibration_date = cal_date_date,
            inventory = inventory_item
        )
        for idx, row in enumerate(reader):
            row_data = row.items()
            for key, value in row_data:
                if key == 'name':
                    calibration_name = value.strip()
                    try:
                        cal_name_item = CoefficientName.objects.get(
                            calibration_name = calibration_name,
                            coeff_name_event =  inventory_item.part.coefficient_name_events.first()
                        )
                    except CoefficientName.DoesNotExist:
                        cal_name_item = None
                    try:
                        config_name_item = ConfigName.objects.get(
                            name = calibration_name,
                            config_name_event =  inventory_item.part.config_name_events.first()
                        )
                    except ConfigName.DoesNotExist:
                        config_name_item = None
                elif key == 'value':
                    valset_keys = {'cal_dec_places': inventory_item.part.cal_dec_places}
                    mock_valset_instance = SimpleNamespace(**valset_keys)
                    raw_valset = str(value)
                    if '[' in raw_valset:
                        raw_valset = raw_valset[1:-1]
                    if 'SheetRef' in raw_valset:
                        ext_finder_filename = "__".join((cal_csv_filename,calibration_name))
                        ref_file = [file for file in ext_files if ext_finder_filename in file.name][0]
                        ref_file.seek(0)
                        reader = io.StringIO(ref_file.read().decode('utf-8'))
                        contents = reader.getvalue()
                        raw_valset = contents
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
        if user_draft.exists():
            draft_users = user_draft
            for user in draft_users:
                csv_event.user_draft.add(user)
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
                parse_valid_coeff_vals(coeff_val_set)
            _create_action_history(csv_event, Action.CALCSVIMPORT, user)
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
            _create_action_history(conf_event, Action.CALCSVIMPORT, user)
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
            _create_action_history(cnst_event, Action.CALCSVIMPORT, user)
        else:
            cnst_event.delete()
    cache.delete('user')
    cache.delete('user_draft')
    cache.delete('ext_files')
    cache.delete('csv_files')



@shared_task(bind=True)
def parse_cruise_files(self):
    cruises_files = cache.get('cruises_files')
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
            # parse out the vessel name to match its formatting from Vessel CSV
            vessel_name_csv = row['ShipName'].strip()
            if vessel_name_csv == 'N/A':
                vessel_name_csv = None

            if vessel_name_csv:
                vessels = Vessel.objects.all()
                for vessel in vessels:
                    if vessel.full_vessel_name == vessel_name_csv:
                        vessel_obj = vessel
                        break
                # Create new Vessel obj if missing
                if not vessel_obj:
                    vessel_obj = Vessel.objects.create(vessel_name = vessel_name_csv)

            # update or create Cruise object based on CUID field
            cruise_obj, created = Cruise.objects.update_or_create(
                CUID = cuid,
                defaults = {
                    'notes': row['notes'],
                    'cruise_start_date': cruise_start_date,
                    'cruise_stop_date': cruise_stop_date,
                    'vessel': vessel_obj,
                },
            )

            if created:
                cruises_created.append(cruise_obj)
            else:
                cruises_updated.append(cruise_obj)
    cache.delete('cruises_files')


@shared_task(bind=True)
def parse_vessel_files(self):
    vessels_files = cache.get('vessels_files')
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
            vessel_name = row['Vessel Name']
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
                vessel_obj, created = Vessel.objects.update_or_create(
                    vessel_name = vessel_name,
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
                    },
                )

                if created:
                    vessels_created.append(vessel_obj)
                else:
                    vessels_updated.append(vessel_obj)
    cache.delete('vessels_files')

@shared_task(bind=True)
def parse_deployment_files(self):
    csv_files = cache.get('dep_files')
    for csv_file in csv_files:
        print(csv_file)
        csv_file.seek(0)
        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
        headers = reader.fieldnames
        deployments = []
        for row in reader:
            if row['mooring.uid'] not in deployments:
                # get Assembly number from RefDes as that seems to be most consistent across CSVs
                ref_des = row['Reference Designator']
                assembly = ref_des.split('-')[0]
                # build data dict
                mooring_uid_dict = {'mooring.uid': row['mooring.uid'], 'assembly': assembly, 'rows': []}
                deployments.append(mooring_uid_dict)

            deployment = next((deployment for deployment in deployments if deployment['mooring.uid']== row['mooring.uid']), False)
            for key, value in row.items():
                deployment['rows'].append({key: value})

        print(deployments[0])
        for row in deployments[0]['rows']:
            print(row)
    cache.delete('dep_files')
