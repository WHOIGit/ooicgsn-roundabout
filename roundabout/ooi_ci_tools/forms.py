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
import io
from types import SimpleNamespace
from decimal import Decimal


from django import forms
from django.db import transaction
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from roundabout.assemblies.models import Assembly
from roundabout.inventory.models import Inventory, Action, Deployment
from roundabout.cruises.models import Cruise, Vessel
from roundabout.locations.models import Location
from roundabout.inventory.utils import _create_action_history
from roundabout.calibrations.models import CoefficientName, CoefficientValueSet, CalibrationEvent, CoefficientNameEvent
from roundabout.calibrations.forms import validate_coeff_vals, parse_valid_coeff_vals
from roundabout.calibrations.utils import reviewer_users
from roundabout.configs_constants.models import ConfigName
from roundabout.users.models import User
from roundabout.userdefinedfields.models import Field, FieldValue
from .models import *
from django.forms.models import inlineformset_factory

                            

# Deployment CSV import config validator
def validate_import_config_deployments(import_config,reader, filename):
    if import_config:
        for idx,row in enumerate(reader):
            try:
                sensor_uid = row['sensor.uid']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Sensor UID'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_sensor_uid:
                if len(sensor_uid) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Sensor UID'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                start_date = row['startDateTime']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Start Date'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_startDateTime:
                if len(start_date) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Start Date'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                stop_date = row['stopDateTime']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Stop Date'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_stopDateTime:
                if len(stop_date) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Stop Date'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                lat = row['lat']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Latitude'),
                    params={'row': idx}
                )
            if import_config.require_deployment_lat:
                if len(lat) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Latitude'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                lon = row['lon']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Longitude'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_lon:
                if len(lon) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Longitude'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                mooring_uid = row['mooring.uid']
                assert mooring_uid != ''
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Mooring UID'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_mooring_uid:
                if len(mooring_uid) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Mooring UID'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                cuid_deploy = row['CUID_Deploy']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse CUID Deploy'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_CUID_Deploy:
                if len(cuid_deploy) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank CUID Deploy'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                node_uid = row['node.uid']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Node UID'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_node_uid:
                if len(node_uid) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Node UID'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                version_number = row['versionNumber']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Version Number'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_versionNumber:
                if len(version_number) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Version Number'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                deployed_by = row['deployedBy']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Deployed By'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_deployedBy:
                if len(deployed_by) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Deployed By'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                CUID_Recover = row['CUID_Recover']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse CUID Recover'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_CUID_Recover:
                if len(CUID_Recover) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank CUID Recover'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                orbit = row['orbit']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Orbit'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_orbit:
                if len(orbit) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Orbit'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                deployment_depth = row['deployment_depth']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Depth'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_deployment_depth:
                if len(deployment_depth) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Depth'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                water_depth = row['water_depth']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Water Depth'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_water_depth:
                if len(water_depth) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Water Depth'),
                        params={'row': idx, 'filename': filename}
                    )
            try:
                notes = row['notes']
            except:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Unable to parse Notes'),
                    params={'row': idx, 'filename': filename}
                )
            if import_config.require_deployment_notes:
                if len(notes) == 0:
                    raise ValidationError(
                        _('File: %(filename)s, Row %(row)s: Import Config disallows blank Notes'),
                        params={'row': idx, 'filename': filename}
                    )
    return True

# Cruise CSV import config validator
def validate_import_config_cruises(import_config, reader, filename):
    for idx, row in enumerate(reader):
        idx = idx + 2
        try:
            ship_name = row['ShipName']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Ship Name'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_cruise_ship_name:
            if len(ship_name) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Ship Name'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            start_date = row['cruiseStartDateTime']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Start Date'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_cruise_cruise_start_date:
            if len(start_date) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Start Date'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            stop_date = row['cruiseStopDateTime']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Stop Date'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_cruise_cruise_end_date:
            if len(stop_date) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Stop Date'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            notes = row['notes']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Notes'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_cruise_notes:
            if len(notes) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Notes'),
                    params={'row': idx, 'filename': filename}
                )
    return True

# Vessel CSV import config validator
def validate_import_config_vessels(import_config, reader, filename):
    for idx, row in enumerate(reader):
        try:
            prefix = row['Prefix']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Prefix'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_vesseldesignation:
            if len(prefix) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Prefix'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            v_des = row['Vessel Designation']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Vessel Designation'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_vesseldesignation:
            if len(v_des) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Vessel Designation'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            v_name = row['Vessel Name']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Vessel Name'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_vessel_name:
            if len(v_name) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Vessel Name'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            ices = row['ICES Code']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse ICES Code'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_ICES_code:
            if len(ices) == 0 or ices == '':
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank ICES Code'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            operator = row['Operator']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Operator'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_operator:
            if len(operator) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Operator'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            call_sign = row['Call Sign']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Call Sign'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_call_sign:
            if len(call_sign) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Call Sign'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            mmsi = row['MMSI#']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse MMSI Number'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_MMSI_number:
            if len(mmsi) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank MMSI Number'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            imo = row['IMO#']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse IMO Number'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_IMO_number:
            if len(imo) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank IMO Number'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            length_m = row['Length (m)']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Length (m)'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_length:
            if len(length_m) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Length (m)'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            max_speed = row['Max Speed (m/s)']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Max Speed (m/s)'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_max_speed:
            if len(max_speed) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Max Speed (m/s)'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            max_draft = row['Max Draft (m)']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Max Draft (m)'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_max_draft:
            if len(max_draft) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Max Draft (m)'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            des = row['Designation']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Designation'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_designation:
            if len(des) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Designation'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            active = row['Active']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse Active'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_active:
            if len(active) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank Active'),
                    params={'row': idx, 'filename': filename}
                )
        try:
            r2r = row['R2R']
        except:
            raise ValidationError(
                _('File: %(filename)s, Row %(row)s: Unable to parse R2R'),
                params={'row': idx, 'filename': filename},
            )
        if import_config.require_vessel_R2R:
            if len(r2r) == 0:
                raise ValidationError(
                    _('File: %(filename)s, Row %(row)s: Import Config disallows blank R2R'),
                    params={'row': idx, 'filename': filename}
                )
    return True

# Handles Deployment CSV file submission and field validation
class ImportDeploymentsForm(forms.Form):
    deployments_csv = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                'multiple': True
            }
        ),
        required=False
    )
    user_draft = forms.ModelMultipleChoiceField(
        queryset = User.objects.all().exclude(groups__name__in=['inventory only']).order_by('username'),
        required=False,
        label = 'Select Reviewers'
    )

    def clean_deployments_csv(self):
        deployments_csv = self.files.getlist('deployments_csv')
        counter = 0
        try:
            import_config = ImportConfig.objects.get(id=1)
        except ImportConfig.DoesNotExist:
            import_config = None
        for csv_file in deployments_csv:
            counter += 1
            filename = csv_file.name
            cache.set('validation_progress', {
                'progress': counter,
                'total': len(deployments_csv),
                'file': filename
            })
            if filename.endswith('_Deploy.csv'):
                try:
                    csv_file.seek(0)
                    reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
                    headers = reader.fieldnames
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to decode file headers'),
                        params={'filename': filename},
                    )
                
                for idx,row in enumerate(reader):
                    try:
                        start_date = row['startDateTime']
                        datetime_obj = parser.parse(start_date)
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Row: %(row)s: Unable to parse Start DateTime'),
                            params={'filename': filename, 'row': idx},
                        )
                    try:
                        stop_date = row['stopDateTime']
                        if len(stop_date) > 0:
                            datetime_obj = parser.parse(stop_date)
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Row: %(row)s: Unable to parse Stop DateTime'),
                            params={'filename': filename, 'row': idx},
                        )
                    try:
                        water_depth = row['water_depth']
                        float_obj = float(water_depth)
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Row: %(row)s: Unable to parse Water Depth'),
                            params={'filename': filename, 'row': idx},
                        )
                    try:
                        mooring_id = row['mooring.uid']
                        dep_number = mooring_id.split('-')[2]
                        assert dep_number != ''
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Row: %(row)s: Unable to parse Mooring UID or Deployment Number from Mooring UID'),
                            params={'filename': filename,  'row': idx},
                        )
                    # get Assembly number from RefDes as that seems to be most consistent across CSVs
                    try:
                        ref_des = row['Reference Designator']
                        ref_des_obj = ReferenceDesignator.objects.get(refdes_name=ref_des)
                    except ReferenceDesignator.DoesNotExist:
                        raise ValidationError( 
                            _('File: %(filename)s: Row: %(row)s: Value: %(value)s: Unable to parse Reference Designator or Reference Designator not found'),
                            params={'filename': filename, 'row': idx, 'value': ref_des},
                        )
                    try:
                        assembly_num = ref_des.split('-')[0]
                        assembly = Assembly.objects.get(assembly_number=assembly_num)
                    except Assembly.DoesNotExist:
                        raise ValidationError(
                            _('File: %(filename)s: Row: %(row)s: Value: %(value)s: Unable to parse Assembly from Reference Designator or Assembly not found'),
                            params={'filename': filename, 'row': idx, 'value': assembly_num},
                        )
                    try:
                        location_code = assembly_num[0:2]
                        deployed_location = Location.objects.get(location_code=location_code)
                    except Location.DoesNotExist:
                        raise ValidationError(
                            _('File: %(filename)s: Row: %(row)s: Value: %(value)s: Unable to parse Location Code or Code not found'),
                            params={'filename': filename, 'row': idx , 'value': location_code},
                        )
                    try:
                        cuid_deploy = row['CUID_Deploy']
                        if '#' in cuid_deploy:
                            continue
                        else:
                            cruise_deployed = Cruise.objects.get(CUID=cuid_deploy)
                    except Cruise.DoesNotExist:
                        raise ValidationError(
                            _('File: %(filename)s: Row: %(row)s: Value: %(value)s: CUID: %(cuid)s: Unable to parse CUID or CUID not found'),
                            params={'filename': filename, 'cuid': cuid_deploy, 'row':idx , 'value': cuid_deploy},
                        )
                validate_import_config_deployments(import_config, reader, filename)
            else:
                raise ValidationError(
                    _('File: %(filename)s: Incorrect filename format. Must be _Deploy.csv'),
                    params={'filename': filename}
                )
        return deployments_csv



# Handles Vessel CSV file submission and field validation
class ImportVesselsForm(forms.Form):
    vessels_csv = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                'multiple': True
            }
        ),
        required=False
    )
    user_draft = forms.ModelMultipleChoiceField(
        queryset = User.objects.all().exclude(groups__name__in=['inventory only']).order_by('username'),
        required=False,
        label = 'Select Reviewers'
    )

    def clean_vessels_csv(self):
        vessels_csv = self.files.getlist('vessels_csv')
        counter = 0
        if vessels_csv:
            try:
                import_config = ImportConfig.objects.get(id=1)
            except ImportConfig.DoesNotExist:
                import_config = None
            try:
                csv_file = vessels_csv[0]
            except:
                raise ValidationError(
                    _('File: Unable to parse CSV file'),
                )
            counter += 1
            filename = csv_file.name
            cache.set('validation_progress',{
                'progress': counter,
                'total': len(vessels_csv),
                'file': filename
            })
            if filename.endswith('shiplist.csv'):
                try:
                    csv_file.seek(0)
                    reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
                    headers = reader.fieldnames
                except:
                    raise ValidationError(
                        _('File: %(filename)s: Unable to decode file headers'),
                        params={'filename': filename},
                    )
                for idx,row in enumerate(reader):
                    try:
                        vessel_name = row['Vessel Name']
                        assert len(vessel_name) > 0
                    except:
                        raise ValidationError(
                            _('File: %(filename)s:  Unable to parse Vessel Name'),
                            params={'filename': filename, },
                        )
                    MMSI_number = None
                    IMO_number = None
                    length = None
                    max_speed = None
                    max_draft = None
                    try:
                        active = row['Active']
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
                        MMSI_number = row['MMSI#']
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Unable to parse MMSI'),
                            params={'filename': filename},
                        )
                    try:
                        IMO_number = row['IMO#']
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Unable to parse IMO'),
                            params={'filename': filename},
                        )
                    try:
                        length = row['Length (m)']
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Unable to parse Lenth (m)'),
                            params={'filename': filename},
                        )
                    try:
                        max_speed = row['Max Draft (m)']
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Unable to parse Max Speed (m/s)'),
                            params={'filename': filename},
                        )
                    try:
                        max_draft = row['Max Draft (m)']
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Unable to parse Max Draft (m)'),
                            params={'filename': filename},
                        )
                    try:
                        ICES_code = row['ICES Code']
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Unable to parse ICES Code'),
                            params={'filename': filename},
                        )
                    # try:
                    #     assert len(ICES_code) > 0 and ICES_code != ''
                    # except:
                    #     raise ValidationError(
                    #         _('File: %(filename)s: Row: %(row)s: Invalid ICES Code. Code must not be blank'),
                    #         params={'filename': filename, 'row': idx},
                    #     )
                    # try:
                    #     assert len(ICES_code) == 4
                    # except:
                    #     raise ValidationError(
                    #         _('File: %(filename)s: Row: %(row)s: Invalid ICES Code. Code must be 4 characters in length'),
                    #         params={'filename': filename, 'row': idx},
                    #     )
                if import_config:
                    validate_import_config_vessels(import_config, reader, filename)
           
        return vessels_csv



# Handles Cruise CSV file submission and field validation
class ImportCruisesForm(forms.Form):
    cruises_csv = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                'multiple': True
            }
        ),
        required=False
    )
    user_draft = forms.ModelMultipleChoiceField(
        queryset = User.objects.all().exclude(groups__name__in=['inventory only']).order_by('username'),
        required=False,
        label = 'Select Reviewers'
    )
    

    def clean_cruises_csv(self):
        cruises_csv = self.files.getlist('cruises_csv')
        counter = 0
        if cruises_csv:
            try:
                import_config = ImportConfig.objects.get(id=1)
            except ImportConfig.DoesNotExist:
                import_config = None
            for csv_file in cruises_csv:
                filename = csv_file.name
                counter += 1
                cache.set('validation_progress',{
                    'progress': counter,
                    'total': len(cruises_csv),
                    'file': filename
                })
                if filename.endswith('CruiseInformation.csv'):
                    try:
                        csv_file.seek(0)
                        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
                        headers = reader.fieldnames
                    except:
                        raise ValidationError(
                            _('File: %(filename)s: Unable to decode file headers'),
                            params={'filename': filename},
                        )
                    if import_config:
                        validate_import_config_cruises(import_config, reader, filename)
                    for row in reader:
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
                            vessel_name_csv = row['ShipName'].strip()
                        except:
                            raise ValidationError(
                                _('File: %(filename)s: Unable to parse Vessel Name'),
                                params={'filename': filename},
                            )     
                
        return cruises_csv


# Validate Calibration CSV field submissions
def validate_cal_files(csv_files,ext_files):
    counter = 0
    try:
        import_config = ImportConfig.objects.get(id=1)
    except ImportConfig.DoesNotExist:
        import_config = None
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
        try:
            deployment = Deployment.objects.filter(
                deployment_to_field_date__year=cal_date_date.year,
                deployment_to_field_date__month=cal_date_date.month,
                deployment_to_field_date__day=cal_date_date.day,
            )
            assert len(deployment) < 2
        except:
            raise ValidationError(
                _('File: %(filename)s, %(value)s: More than one existing Deployment associated with File Deployment Date'),
                params={'value': cal_date_string, 'filename': cal_csv.name},
            )
        try:
            custom_field = Field.objects.get(field_name='Manufacturer Serial Number')
        except:
            raise ValidationError(
                _('Global Custom Field "Manufacturer Serial Number" must be created prior to import'),
            )
        try:
            inv_manufacturer_serial = FieldValue.objects.get(inventory=inventory_item,field=custom_field,is_current=True)
        except FieldValue.DoesNotExist:
            inv_keys = {'field_value': ''}
            inv_manufacturer_serial = SimpleNamespace(**inv_keys)
        for idx, row in enumerate(reader):
            row_data = row.items()
            for key, value in row_data:
                if key == 'serial':
                    try:
                        csv_manufacturer_serial = value.strip()
                    except:
                        raise ValidationError(
                            _('File: %(filename)s, Row %(row)s: Cannot parse Manufacturer Serial Number'),
                            params={'row': idx, 'filename': cal_csv.name},
                        )
                    if len(inv_manufacturer_serial.field_value) > 0 and len(csv_manufacturer_serial) > 0:
                        try:
                            assert csv_manufacturer_serial == inv_manufacturer_serial.field_value
                        except:
                            raise ValidationError(
                                _('File: %(filename)s, Row %(row)s: Manufacturer Serial Number differs between Inventory Item (%(inv_msn)s) and file (%(csv_msn)s)'),
                                params={'row': idx, 'filename': cal_csv.name, 'inv_msn': inv_manufacturer_serial.field_value, 'csv_msn':csv_manufacturer_serial},
                            )
                if key == 'name':
                    calibration_name = value.strip()
                    try:
                        assert len(calibration_name) > 0
                    except:
                        raise ValidationError(
                            _('File: %(filename)s, Calibration Name: %(value)s, Row %(row)s: Calibration Name is blank'),
                            params={'value': calibration_name, 'row': idx, 'filename': cal_csv.name},
                        )
                    try:
                        cal_name_item = CoefficientName.objects.get(
                            calibration_name = calibration_name,
                            coeff_name_event =  inventory_item.part.part_coefficientnameevents.first()
                        )
                    except CoefficientName.DoesNotExist:
                        calname_keys = {'value_set_type': 'sl', 'threshold_low': None, 'threshold_high': None}
                        cal_name_item = SimpleNamespace(**calname_keys)
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
                    if import_config.require_calibration_coefficient_values:
                        try:
                            assert len(raw_valset) > 0
                        except:
                            raise ValidationError(
                                _('File: %(filename)s, Row %(row)s: Import Config disallows blank Calibration Coefficient value(s)'),
                                params={'row': idx, 'filename': cal_csv.name}
                            )
                    threshold = None
                    if hasattr(cal_name_item,'thresholds') and import_config.require_calibration_coefficient_threshold:
                        threshold = cal_name_item.thresholds.first()
                    if cal_name_item.threshold_low and cal_name_item.threshold_high and import_config.require_calibration_coefficient_threshold:
                        threshold_keys = {'low': cal_name_item.threshold_low, 'high': cal_name_item.threshold_high}
                        threshold = SimpleNamespace(**threshold_keys)
                    if '[' in raw_valset:
                        raw_valset = raw_valset[1:-1]
                        cal_name_item.value_set_type = '1d'
                    if 'SheetRef' in raw_valset:
                        ext_finder_filename = "__".join((cal_csv_filename,calibration_name))
                        cal_name_item.value_set_type = '2d'
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
                        validate_coeff_vals(mock_valset_instance, cal_name_item.value_set_type, raw_valset, filename = ref_file.name, cal_name = calibration_name, threshold = threshold)
                    else:
                        validate_coeff_vals(mock_valset_instance, cal_name_item.value_set_type, raw_valset, filename = cal_csv.name, cal_name = calibration_name, threshold = threshold)
                elif key == 'notes':
                    try:
                        notes = value.strip()
                    except:
                        raise ValidationError(
                            _('File: %(filename)s, Calibration Name: %(value)s, Row %(row)s: Unable to parse Calibration Coefficient note(s)'),
                            params={'value': calibration_name, 'row': idx, 'filename': cal_csv.name},
                        )
                    if import_config.require_calibration_notes:
                        try:
                            assert len(notes) > 0
                        except:
                            raise ValidationError(
                                _('File: %(filename)s, Row %(row)s: Import Config disallows blank Calibration Notes'),
                                params={'row': idx, 'filename': cal_csv.name}
                            )

# Handles Calibration CSV file submission and field validation
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


# Handles Comment form submission
class CommentForm(forms.ModelForm):
    class Meta:
        model = MPTTComment
        fields = ['detail',]
        labels = {
            'detail': 'Provide your comment here:'
        }


# Handles Action-History-level Comment form submission
class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ['detail',]

# CSV Import Configuration form 
# Inputs: All fields from Calibration, Deployment, Cruise, and Vessel CSV's
class ImportConfigForm(forms.ModelForm):
    class Meta:
        model = ImportConfig 
        fields = '__all__'
        labels = {
            'require_calibration_coefficient_values': 'Coefficient value(s)',
            'require_calibration_notes': 'Notes',
            'require_calibration_coefficient_threshold': 'Threshold Validation',
            'require_deployment_sensor_uid': 'Sensor UID',
            'require_deployment_startDateTime': 'Start Date',
            'require_deployment_stopDateTime': 'Stop Date',
            'require_deployment_lat': 'Latitude',
            'require_deployment_lon': 'Longitude',
            'require_deployment_mooring_uid': 'Mooring UID',
            'require_deployment_CUID_Deploy': 'CUID Deploy',
            'require_deployment_node_uid': 'Node UID',
            'require_deployment_versionNumber': 'Version Number',
            'require_deployment_deployedBy': 'Deployed By',
            'require_deployment_CUID_Recover': 'CUID Recover',
            'require_deployment_orbit': 'Orbit',
            'require_deployment_deployment_depth': 'Depth',
            'require_deployment_water_depth': 'Water Depth',
            'require_deployment_notes': 'Notes',
            'require_cruise_ship_name': 'Ship Name',
            'require_cruise_cruise_start_date': 'Start Date',
            'require_cruise_cruise_end_date': 'Stop Date',
            'require_cruise_notes': 'Notes',
            'require_vessel_vesseldesignation': 'Vessel Designation',
            'require_vessel_designation': 'Designation',
            'require_vessel_vessel_name': 'Vessel Name',
            'require_vessel_ICES_code': 'ICES Code',
            'require_vessel_operator': 'Operator',
            'require_vessel_call_sign': 'Call Sign',
            'require_vessel_MMSI_number': 'MMSI Number',
            'require_vessel_IMO_number': 'IMO Number',
            'require_vessel_length': 'Length (m)',
            'require_vessel_max_speed': 'Max Speed (m/s)',
            'require_vessel_max_draft': 'Max Draft (m)',
            'require_vessel_active': 'Active',
            'require_vessel_R2R': 'R2R'
        }
    def __init__(self, *args, **kwargs):
        super(ImportConfigForm, self).__init__(*args, **kwargs)

    def save(self, commit = True): 
        import_config = super(ImportConfigForm, self).save(commit = False)
        if commit:
            import_config.save()
            return import_config


# Handles Reference Designator CSV file submission and field validation
class ImportReferenceDesignatorForm(forms.Form):
    refdes_csv = forms.FileField(
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

    def clean_refdes_csv(self):
        refdes_files = self.files.getlist('refdes_csv')
        for csv_file in refdes_files:
            csv_file.seek(0)
            reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
            filename = csv_file.name
            headers = reader.fieldnames
            if 'Reference_Designator' in headers:
                for idx, row in enumerate(reader):
                    row_idx = idx + 1
                    refdes_name = row['Reference_Designator']
                    # validate_reference_designator(refdes_name, row_idx)
            else:
                raise ValidationError(
                    _('File: %(filename)s:  Reference Designator CSV file is not valid. Must contain a Reference_Designator column.'),
                        params={'filename': filename},
                    )        
        return refdes_files



# Handles Bulk Upload CSV file submission and field validation
class ImportBulkUploadForm(forms.Form):
    bulk_csv = forms.FileField(
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

    def clean_bulk_csv(self):
        bulk_files = self.files.getlist('bulk_csv')
        
        for csv_file in bulk_files:
            csv_file.seek(0)
            reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
            file_name = csv_file.name
            if file_name.endswith('-AssetRecord.csv'):
                pass
                # for row in reader:
                #     try:
                #         asset_uid = row['ASSET_UID']
                #         inv_item = Inventory.objects.get(serial_number = asset_uid)
                #     except Inventory.DoesNotExist:
                #         raise ValidationError(
                #                 _('File: %(filename)s, Asset UID %(row)s: No matching Inventory serial number exists'),
                #                 params={'row': asset_uid, 'filename': file_name}
                #             )
            elif file_name.endswith('_vocab.csv'):
                pass
                # for row in reader:
                #     manufacturer = row['Manufacturer']
                #     asset_model = row['Model']
                #     man_field_list = FieldValue.objects.filter(field__field_name__iexact='Manufacturer', field_value = manufacturer, part__isnull=False, is_current=True)
                #     mod_field_list = FieldValue.objects.filter(field__field_name__iexact='Model', field_value = asset_model, part__isnull=False, is_current=True)
                #     if not len(man_field_list):
                #         raise ValidationError(
                #                 _('File: %(filename)s, Manufacturer %(manufacturer)s: No matching Manufacturer exists'),
                #                 params={'manufacturer': manufacturer,'filename': file_name}
                #             )
                #     if not len(mod_field_list):
                #         raise ValidationError(
                #                 _('File: %(filename)s, Manufacturer %(manufacturer)s, Model %(model)s: No matching Model exists'),
                #                 params={'manufacturer': manufacturer, 'model': asset_model, 'filename': file_name}
                #             )
                #     if len(man_field_list) and len(mod_field_list):
                #         man_field_obj = man_field_list.first()
                #         mod_field_obj = mod_field_list.first()
                #         if man_field_obj.part != mod_field_obj.part:
                #             raise ValidationError(
                #                 _('File: %(filename)s, Manufacturer %(manufacturer)s, Model %(model)s: No matching Part exists for Manufacturer/Model pair'),
                #                 params={'manufacturer': manufacturer, 'model': asset_model, 'filename': file_name}
                #             )
            
            else:
                raise ValidationError(
                        _('File: %(filename)s: File is invalid format. File must be of type -AssetRecord or _vocab'),
                        params={ 'filename': file_name}
                    )

        return bulk_files


# Handeles Reference Designator name validation
def validate_reference_designator(name, row_idx = None):
    assertion_sets = name.split('-')
    if len(assertion_sets) == 4:
        try:
            first_section = assertion_sets[0]
            assert type(first_section) is str
            assert len(first_section) == 8 
        except:
            raise ValidationError(
                _('Row: %(row_num)s, Reference Designator: %(name)s: First section should be an 8-character string'),
                params={'name': name, 'row_num': row_idx}
            )
        try:
            second_section = assertion_sets[1]
            assert type(second_section) is str
            assert len(second_section) == 5
        except:
            raise ValidationError(
                _('Row: %(row_num)s, Reference Designator: %(name)s: Second section should be a 5-character string'),
                params={'name': name, 'row_num': row_idx}
            )
        try:
            third_section = assertion_sets[2]
            assert len(third_section) == 2
            intable_2 = int(third_section)
            assert type(intable_2) is int
        except:
            raise ValidationError(
                _('Row: %(row_num)s, Reference Designator: %(name)s: Third section should be a 2-digit integer'),
                params={'name': name, 'row_num': row_idx}
            )
        try:
            fourth_section = assertion_sets[3]
            assert type(fourth_section) is str
            assert len(fourth_section) == 9
        except:
            raise ValidationError(
                _('Row: %(row_num)s, Reference Designator: %(name)s: Fourth section should be a 9-character string'),
                params={'name': name, 'row_num': row_idx}
            )



# Event form
# Inputs: Effective Date and Approval
class BulkUploadEventForm(forms.ModelForm):
    class Meta:
        model = BulkUploadEvent
        fields = ['user_draft']
        labels = {
            'user_draft': 'Reviewers'
        }
        widgets = {
            'user_draft': forms.SelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super(BulkUploadEventForm, self).__init__(*args, **kwargs)
        self.fields['user_draft'].queryset = reviewer_users()

    def clean_user_draft(self):
        user_draft = self.cleaned_data.get('user_draft')
        return user_draft

    def save(self, commit = True):
        event = super(BulkUploadEventForm, self).save(commit = False)
        if commit:
            event.save()
            if event.user_approver.exists():
                for user in event.user_approver.all():
                    event.user_draft.add(user)
                    event.user_approver.remove(user)
            event.save()
            return event


# Bulk Asset Record form
class BulkAssetForm(forms.ModelForm):
    class Meta:
        model = BulkAssetRecord
        fields = '__all__'
        exclude = ('bulk_file','id','created_at')
        labels = {}
        widgets = {
            'bulk_file': forms.Select(
                attrs = {
                    'readonly': True,
                    'style': 'cursor: not-allowed; pointer-events: none; background-color: #d5dfed;'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super(BulkAssetForm, self).__init__(*args, **kwargs)
    def save(self, commit=True):
        bulk_asset = super(BulkAssetForm, self).save(commit = False)
        if commit:
            bulk_asset.save()
        return bulk_asset


# Bulk Vocab Record form
class BulkVocabForm(forms.ModelForm):
    class Meta:
        model = BulkVocabRecord
        fields = '__all__'
        exclude = ('bulk_file','id', 'created_at')
        labels = {}
        widgets = {
            'bulk_file': forms.Select(
                attrs = {
                    'readonly': True,
                    'style': 'cursor: not-allowed; pointer-events: none; background-color: #d5dfed;'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super(BulkVocabForm, self).__init__(*args, **kwargs)
    def save(self, commit=True):
        bulk_vocab = super(BulkVocabForm, self).save(commit = False)
        if commit:
            bulk_vocab.save()
        return bulk_vocab


# Asset Record form instance generator for Bulk Upload Events
EventAssetFileFormset = inlineformset_factory(
    BulkUploadEvent,
    BulkAssetRecord,
    form=BulkAssetForm,
    fields='__all__',
    extra=0,
    can_delete=True
)

# Vocab Record form instance generator for Bulk Upload Events
EventVocabFileFormset = inlineformset_factory(
    BulkUploadEvent,
    BulkVocabRecord,
    form=BulkVocabForm,
    fields='__all__',
    extra=0,
    can_delete=True
)