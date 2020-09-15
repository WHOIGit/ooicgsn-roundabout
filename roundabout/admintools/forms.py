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
import datetime
from types import SimpleNamespace

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


from .models import Printer
from roundabout.inventory.models import Inventory, Action
from roundabout.inventory.utils import _create_action_history
from roundabout.calibrations.models import CoefficientName, CoefficientValueSet, CalibrationEvent
from roundabout.calibrations.forms import validate_coeff_vals, parse_valid_coeff_vals
from roundabout.users.models import User


class ImportInventoryForm(forms.Form):
    document = forms.FileField()

class ImportCalibrationForm(forms.Form):
    cal_csv = forms.FileField()
    user_draft = forms.ModelMultipleChoiceField(
        queryset = User.objects.all().exclude(groups__name__in=['inventory only']).order_by('username'),
        required=False,
        label = 'Select Reviewers'
    )

    def clean_cal_csv(self):
        cal_csv = self.cleaned_data['cal_csv']
        cal_csv.seek(0)
        reader = csv.DictReader(io.StringIO(cal_csv.read().decode('utf-8')))
        headers = reader.fieldnames
        try:
            inv_serial = cal_csv.name.split('__')[0]
            inventory_item = Inventory.objects.get(serial_number=inv_serial)
        except:
            raise ValidationError(
                _('%(value)s: Unable to find Inventory item with this Serial Number'),
                params={'value': inv_serial},
            )
        try:
            cal_date_string = cal_csv.name.split('__')[1][:8]
            cal_date_date = datetime.datetime.strptime(cal_date_string, "%Y%m%d").date()
        except:
            raise ValidationError(
                _('%(value)s: Unable to parse Calibration Date from Filename'),
                params={'value': cal_date_string},
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
                            _('Row %(row)s, %(value)s: Unable to find Calibration item with this Name'),
                            params={'value': calibration_name, 'row': idx},
                        )
                elif key == 'value':
                    valset_keys = {'cal_dec_places': inventory_item.part.cal_dec_places}
                    mock_valset_instance = SimpleNamespace(**valset_keys)
                    try:
                        raw_valset = str(value)
                        if '[' in raw_valset:
                            raw_valset = raw_valset[1:-1]
                        if 'SheetRef' in raw_valset:
                            raw_valset = ''
                    except:
                        raise ValidationError(
                            _('Row %(row)s: Unable to parse Calibration Coefficient value(s)'),
                            params={'row': idx},
                        )
                    validate_coeff_vals(mock_valset_instance, cal_name_item.value_set_type, raw_valset)
                elif key == 'notes':
                    try:
                        notes = value.strip()
                    except:
                        raise ValidationError(
                            _('Row %(row)s: Unable to parse Calibration Coefficient note(s)'),
                            params={'row': idx},
                        )
        return cal_csv


class PrinterForm(forms.ModelForm):

    class Meta:
        model = Printer
        fields = ['name', 'ip_domain', 'printer_type' ]
        labels = {
        'ip_domain': 'IP Address/Domain'
    }
