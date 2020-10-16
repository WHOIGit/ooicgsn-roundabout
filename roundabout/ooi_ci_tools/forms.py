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
import re
import requests
from dateutil import parser
import datetime
from types import SimpleNamespace
from decimal import Decimal


from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache


from roundabout.inventory.models import Inventory, Action
from roundabout.cruises.models import Cruise, Vessel
from roundabout.inventory.utils import _create_action_history
from roundabout.calibrations.models import CoefficientName, CoefficientValueSet, CalibrationEvent
from roundabout.calibrations.forms import validate_coeff_vals, parse_valid_coeff_vals
from roundabout.users.models import User


class ImportDeploymentsForm(forms.Form):
    deployments_csv = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                'multiple': True
            }
        ),
        required=False
    )

    def clean_deployments_csv(self):
        deployments_csv = self.files.getlist('deployments_csv')
        counter = 0
        for csv_file in deployments_csv:
            counter += 1
            filename = csv_file.name[:-4]
            cache.set('validation_progress',{
                'progress': counter,
                'total': len(deployments_csv),
                'file': filename
            })
            try:
                csv_file.seek(0)
                reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
                headers = reader.fieldnames
            except:
                raise ValidationError(
                    _('File: %(filename)s: Unable to decode file headers'),
                    params={'filename': filename},
                )
            deployments = []
            for row in reader:
                try:
                    mooring_id = row['mooring.uid']
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse Mooring UID'),
                        params={'filename': filename},
                    )
                if mooring_id not in deployments:
                    # get Assembly number from RefDes as that seems to be most consistent across CSVs
                    try:
                        ref_des = row['Reference Designator']
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Unable to parse Reference Designator'),
                            params={'filename': filename},
                        )
                    try:
                        assembly = ref_des.split('-')[0]
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Unable to parse Assembly from Reference Designator'),
                            params={'filename': filename},
                        )
                    # build data dict
                    mooring_uid_dict = {'mooring.uid': row['mooring.uid'], 'assembly': assembly, 'rows': []}
                    deployments.append(mooring_uid_dict)
                deployment = next((deployment for deployment in deployments if deployment['mooring.uid']== row['mooring.uid']), False)
                for key, value in row.items():
                    deployment['rows'].append({key: value})
        return deployments_csv


class ImportVesselsForm(forms.Form):
    vessels_csv = forms.FileField(required=False)

    def clean_vessels_csv(self):
        vessels_csv = self.files.getlist('vessels_csv')
        counter = 0
        for csv_file in vessels_csv:
            try:
                csv_file.seek(0)
                filename = csv_file.name[:-4]
                reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
                headers = reader.fieldnames
                total_rows = len(list(reader))
            except:
                raise ValidationError(
                    _('File: %(filename)s: Unable to decode file headers'),
                    params={'filename': filename},
                )
            for row in reader:
                counter += 1
                cache.set('validation_progress',{
                    'progress': counter,
                    'total': total_rows,
                    'file': filename
                })
                try:
                    vessel_name = row['Vessel Name']
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse Vessel Name'),
                        params={'filename': filename},
                    )
                MMSI_number = None
                IMO_number = None
                length = None
                max_speed = None
                max_draft = None
                try:
                    active = re.sub(r'[()]', '', row['Active'])
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse Active'),
                        params={'filename': filename},
                    )
                try:
                    R2R = row['R2R']
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse R2R'),
                        params={'filename': filename},
                    )
                try:
                    if row['MMSI#']:
                        MMSI_number = int(re.sub('[^0-9]','', row['MMSI#']))
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse MMSI'),
                        params={'filename': filename},
                    )
                try:
                    if row['IMO#']:
                        IMO_number = int(re.sub('[^0-9]','', row['IMO#']))
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse IMO'),
                        params={'filename': filename},
                    )
                try:
                    if row['Length (m)']:
                        length = Decimal(row['Length (m)'])
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse Lenth (m)'),
                        params={'filename': filename},
                    )
                try:
                    if row['Max Speed (m/s)']:
                        max_speed = Decimal(row['Max Draft (m)'])
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse Max Speed (m/s)'),
                        params={'filename': filename},
                    )
                try:
                    if row['Max Draft (m)']:
                        max_draft = Decimal(row['Max Draft (m)'])
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse Max Draft (m)'),
                        params={'filename': filename},
                    )
        return vessels_csv


class ImportCruisesForm(forms.Form):
    cruises_csv = forms.FileField(required=False)

    def clean_cruises_csv(self):
        cruises_csv = self.files.getlist('cruises_csv')
        for csv_file in cruises_csv:
            filename = csv_file.name[:-4]
            counter = 0
            try:
                csv_file.seek(0)
                reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
                headers = reader.fieldnames
                total_rows = len(list(reader))
            except:
                raise ValidationError(
                    _('File: %(filename)s: Unable to decode file headers'),
                    params={'filename': filename},
                )
            for row in reader:
                counter += 1
                cache.set('validation_progress',{
                    'progress': counter,
                    'total': total_rows,
                    'file': filename
                })
                try:
                    cuid = row['CUID']
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse CUID'),
                        params={'filename': filename},
                    )
                try:
                    cruise_start_date = parser.parse(row['cruiseStartDateTime']).date()
                    cruise_stop_date = parser.parse(row['cruiseStopDateTime']).date()
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse Cruise Start/Stop Dates'),
                        params={'filename': filename},
                    )
                try:
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
                                pass
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to parse Vessel Name'),
                        params={'filename': filename},
                    )     
        return cruises_csv



def validate_cal_files(csv_files,ext_files):
    counter = 0
    for cal_csv in csv_files:
        counter += 1
        cal_csv_filename = cal_csv.name[:-4]
        cache.set('validation_progress',{
            'progress': counter,
            'total': len(csv_files),
            'file': cal_csv_filename
        })
        cal_csv.seek(0)
        reader = csv.DictReader(io.StringIO(cal_csv.read().decode('utf-8')))
        headers = reader.fieldnames
        try:
            inv_serial = cal_csv.name.split('__')[0]
            inventory_item = Inventory.objects.get(serial_number=inv_serial)
        except:
            raise ValidationError(
                _('File: %(filename)s, %(value)s: Unable to find Inventory item with this Serial Number'),
                params={'value': inv_serial, 'filename': cal_csv.name},
            )
        try:
            cal_date_string = cal_csv.name.split('__')[1][:8]
            cal_date_date = datetime.datetime.strptime(cal_date_string, "%Y%m%d").date()
        except:
            raise ValidationError(
                _('File: %(filename)s, %(value)s: Unable to parse Calibration Date from Filename'),
                params={'value': cal_date_string, 'filename': cal_csv.name},
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
                    except:
                        raise ValidationError(
                            _('File: %(filename)s, Calibration Name: %(value)s, Row %(row)s: Unable to find Calibration item with this Name'),
                            params={'value': calibration_name, 'row': idx, 'filename': cal_csv.name},
                        )
                elif key == 'value':
                    valset_keys = {'cal_dec_places': inventory_item.part.cal_dec_places}
                    mock_valset_instance = SimpleNamespace(**valset_keys)
                    try:
                        raw_valset = str(value)
                    except:
                        raise ValidationError(
                            _('File: %(filename)s, Calibration Name: %(value)s, Row %(row)s, %(value)s: Unable to parse Calibration Coefficient value(s)'),
                            params={'value': calibration_name,'row': idx, 'filename': cal_csv.name},
                        )
                    if '[' in raw_valset:
                        raw_valset = raw_valset[1:-1]
                    if 'SheetRef' in raw_valset:
                        ext_finder_filename = "__".join((cal_csv_filename,calibration_name))
                        try:
                            ref_file = [file for file in ext_files if ext_finder_filename in file.name][0]
                            assert len(ref_file) > 0
                        except:
                            raise ValidationError(
                                _('File: %(filename)s, Calibration Name: %(value)s, Row %(row)s: No associated .ext file selected'),
                                params={'value': calibration_name, 'row': idx, 'filename': cal_csv.name},
                            )
                        ref_file.seek(0)
                        reader = io.StringIO(ref_file.read().decode('utf-8'))
                        contents = reader.getvalue()
                        raw_valset = contents
                        validate_coeff_vals(mock_valset_instance, cal_name_item.value_set_type, raw_valset, filename = ref_file.name, cal_name = calibration_name)
                    else:
                        validate_coeff_vals(mock_valset_instance, cal_name_item.value_set_type, raw_valset, filename = cal_csv.name, cal_name = calibration_name)
                elif key == 'notes':
                    try:
                        notes = value.strip()
                    except:
                        raise ValidationError(
                            _('File: %(filename)s, Calibration Name: %(value)s, Row %(row)s: Unable to parse Calibration Coefficient note(s)'),
                            params={'value': calibration_name, 'row': idx, 'filename': cal_csv.name},
                        )


class ImportCalibrationForm(forms.Form):
    calibration_csv = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                'multiple': True
            }
        ),
        required = False
    )
    user_draft = forms.ModelMultipleChoiceField(
        queryset = User.objects.all().exclude(groups__name__in=['inventory only']).order_by('username'),
        required=False,
        label = 'Select Reviewers'
    )

    def clean_calibration_csv(self):
        cal_files = self.files.getlist('calibration_csv')
        csv_files = []
        ext_files = []
        for file in cal_files:
            ext = file.name[-3:]
            if ext == 'ext':
                ext_files.append(file)
            if ext == 'csv':
                csv_files.append(file)
        validate_cal_files(csv_files,ext_files)
        return cal_files