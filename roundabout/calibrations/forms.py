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

from bootstrap_datepicker_plus import DatePickerInput
from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from sigfig import round

from roundabout.inventory.models import Inventory
from roundabout.parts.models import Part
from roundabout.users.models import User
from .models import CoefficientName, CoefficientValueSet, CalibrationEvent, CoefficientValue, CoefficientNameEvent, CalibrationEventHyperlink
from .utils import reviewer_users


# Event form
# Inputs: Effective Date and Approval
class CalibrationEventForm(forms.ModelForm):
    class Meta:
        model = CalibrationEvent
        fields = ['calibration_date','user_draft']
        labels = {
            'calibration_date': 'Calibration Date',
            'user_draft': 'Reviewers'
        }
        widgets = {
            'calibration_date': DatePickerInput(
                options={
                    "format": "MM/DD/YYYY",
                    "showClose": True,
                    "showClear": True,
                    "showTodayButton": True,
                }
            ),
            'user_draft': forms.SelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super(CalibrationEventForm, self).__init__(*args, **kwargs)
        self.fields['user_draft'].queryset = reviewer_users()

    def clean_user_draft(self):
        user_draft = self.cleaned_data.get('user_draft')
        return user_draft

    def save(self, commit = True):
        event = super(CalibrationEventForm, self).save(commit = False)
        if commit:
            event.save()
            if event.user_approver.exists():
                for user in event.user_approver.all():
                    event.user_draft.add(user)
                    event.user_approver.remove(user)
            event.save()
            return event


# CoefficientName Event form
# Inputs: Reviewers
class CoefficientNameEventForm(forms.ModelForm):
    class Meta:
        model = CoefficientNameEvent
        fields = ['user_draft']
        labels = {
            'user_draft': 'Reviewers'
        }
        widgets = {
            'user_draft': forms.SelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super(CoefficientNameEventForm, self).__init__(*args, **kwargs)
        self.fields['user_draft'].queryset = reviewer_users()

    def clean_user_draft(self):
        user_draft = self.cleaned_data.get('user_draft')
        return user_draft

    def save(self, commit = True):
        event = super(CoefficientNameEventForm, self).save(commit = False)
        if commit:
            event.save()
            if event.user_approver.exists():
                for user in event.user_approver.all():
                    event.user_draft.add(user)
                    event.user_approver.remove(user)
            event.save()
            return event



# CoefficientValueSet form
# Inputs: Coefficient values and notes per Part Calibration
class CoefficientValueSetForm(forms.ModelForm):
    class Meta:
        model = CoefficientValueSet
        fields = ['coefficient_name','value_set', 'notes']
        labels = {
            'coefficient_name': 'Calibration Name',
            'value_set': 'Calibration Coefficient(s)',
            'notes': 'Additional Notes'
        }
        widgets = {
            'coefficient_name': forms.Select(
                attrs = {
                    'readonly': True,
                    'style': 'cursor: not-allowed; pointer-events: none; background-color: #d5dfed;'
                }
            ),
            'value_set': forms.Textarea(
                attrs = {
                    'style': 'white-space: nowrap'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        if 'inv_id' in kwargs:
            self.inv_id = kwargs.pop('inv_id')
        super(CoefficientValueSetForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'inv_id'):
            inv_inst = Inventory.objects.get(id = self.inv_id)
            self.instance.cal_dec_places = inv_inst.part.cal_dec_places
            self.instance.part = inv_inst.part

    def clean_value_set(self):
        raw_set = self.cleaned_data.get('value_set')
        coefficient_name = self.cleaned_data.get('coefficient_name')
        try:
            cal_obj = CoefficientName.objects.get(coeff_name_event = self.instance.part.coefficient_name_events.first(), calibration_name = coefficient_name)
            set_type =  cal_obj.value_set_type
        except:
            raise ValidationError(
                _('Unable to query selected Calibration instance'),
            )
        else:
            return validate_coeff_vals(self.instance, set_type, raw_set)

    def save(self, commit=True):
        value_set = super(CoefficientValueSetForm, self).save(commit = False)
        if commit:
            value_set.save()
            parse_valid_coeff_vals(value_set)
        return value_set


# CalibrationName Form
# Inputs: Name, Input Type, Significant Figures
class CoefficientNameForm(forms.ModelForm):
    class Meta:
        model = CoefficientName
        fields = ['calibration_name', 'value_set_type', 'sigfig_override', 'deprecated', 'threshold_low','threshold_high']
        labels = {
            'calibration_name': 'Name',
            'value_set_type': 'Type',
            'sigfig_override': 'Significant Figures',
            'deprecated': 'Deprecated',
            'threshold_low': 'Coefficient Threshold (Low)',
            'threshold_high': 'Coefficient Threshold (High)'
        }
        widgets = {
            'deprecated': forms.CheckboxInput()
        }

    def __init__(self, *args, **kwargs):
        super(CoefficientNameForm, self).__init__(*args, **kwargs)
        if self.instance.deprecated:
            self.fields['calibration_name'].widget.attrs.update(
                {
                    'readonly': True,
                    'style': 'cursor: not-allowed; pointer-events: none; background-color: #d5dfed;'
                }
            )

    def clean_sigfig_override(self):
        raw_sigfig = self.cleaned_data.get('sigfig_override')
        try:
            assert 1 <= raw_sigfig <= 32
        except:
            raise ValidationError(
                    _('Input must be between 1 and 32.')
                )
        else:
            return raw_sigfig

    def clean_threshold_low(self):
        threshold_low = self.cleaned_data.get('threshold_low')
        try:
            regular_val = round(threshold_low.strip(), notation = 'std', output_type=float)
        except:
            raise ValidationError(
                    _('Input cannot be coerced into a number')
                )
        else:
            return threshold_low

    def clean_threshold_high(self):
        threshold_high = self.cleaned_data.get('threshold_high')
        try:
            regular_val = round(threshold_high.strip(), notation = 'std', output_type=float)
        except:
            raise ValidationError(
                    _('Input cannot be coerced into a number')
                )
        else:
            return threshold_high


# CoefficientValue form
# Inputs: Coefficient values, significant figures, and notation format per CoefficientValueSet
class CoefficientValueForm(forms.ModelForm):
    class Meta:
        model = CoefficientValue
        fields = ['value','sigfig', 'notation_format', 'original_value']
        labels = {
            'original_value': 'Coefficient Value',
            'sigfig': 'Significant Digits',
            'notation_format': 'Notation Format'
        }
        widgets = {
            'original_value': forms.TextInput(
                attrs = {
                    'readonly': True,
                    'style': 'cursor: not-allowed; background-color: #d5dfed;'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        if 'valset_id' in kwargs:
            self.valset_id = kwargs.pop('valset_id')
        super(CoefficientValueForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'valset_id'):
            valset_inst = CoefficientValueSet.objects.get(id = self.valset_id)
            self.instance.part_dec_places = valset_inst.calibration_event.inventory.part.cal_dec_places

    def clean_value(self):
        val = self.cleaned_data.get('value')
        return val

    def clean_original_value(self):
        orig_val = self.cleaned_data.get('original_value')
        return orig_val

    def save(self, commit = True):
        coeff_val_inst = super(CoefficientValueForm, self).save(commit = False)
        coeff_val_inst.value = round(
            coeff_val_inst.original_value,
            sigfigs = coeff_val_inst.sigfig,
            notation = coeff_val_inst.notation_format
        )
        coeff_val_inst.save()
        return coeff_val_inst


# Calibration Copy Form
# Inputs: Part
class CalPartCopyForm(forms.Form):
    part_select = forms.ModelChoiceField(
        queryset = Part.objects.filter(part_type__ccc_toggle=True),
        required=False,
        label = 'Copy Calibrations from Part'
    )

    def __init__(self, *args, **kwargs):
        self.part_id = kwargs.pop('part_id')
        super(CalPartCopyForm, self).__init__(*args, **kwargs)
        self.fields['part_select'].queryset = Part.objects.filter(part_type__ccc_toggle=True,coefficient_name_events__gt=0).exclude(id__in=str(self.part_id))

    def clean_part_select(self):
        part_select = self.cleaned_data.get('part_select')
        to_part = Part.objects.get(id=self.part_id)
        if part_select is not None:
            validate_part_select(to_part, part_select)
        return part_select

    def save(self):
        part_select = self.cleaned_data.get('part_select')
        if self.has_changed():
            copy_to_id = self.part_id
            copy_from_id = part_select.id
            copy_calibrations(copy_to_id, copy_from_id)
        return part_select


# Coefficient ValueSet form instance generator for CalibrationEvents
EventValueSetFormset = inlineformset_factory(
    CalibrationEvent,
    CoefficientValueSet,
    form=CoefficientValueSetForm,
    fields=('coefficient_name', 'value_set', 'notes'),
    extra=0,
    can_delete=True
)

CalibrationEventHyperlinkFormset = forms.models.inlineformset_factory(
    CalibrationEvent, CalibrationEventHyperlink, fields=('text', 'url'), extra=1, can_delete=True)


# Coefficient Name form instance generator for Parts
PartCalNameFormset = inlineformset_factory(
    CoefficientNameEvent,
    CoefficientName,
    form=CoefficientNameForm,
    fields=('calibration_name', 'value_set_type', 'sigfig_override', 'deprecated', 'threshold_low', 'threshold_high'),
    extra=1,
    can_delete=True
)

# Coefficient Value form instance generator for CoefficientValueSets
ValueSetValueFormset = inlineformset_factory(
    CoefficientValueSet,
    CoefficientValue,
    form=CoefficientValueForm,
    fields=('original_value', 'sigfig', 'notation_format'),
    extra=0,
    can_delete=True
)

# Validator for 1-D, comma-separated Coefficient value arrays
def validate_coeff_array(coeff_1d_array, valset_inst, val_set_index = 0, filename = '', cal_name = '', threshold = None):
    error_row_index = val_set_index + 1
    if threshold:
        low = float(threshold.low)
        high = float(threshold.high)
    else:
        low = float(-1000000000)
        high = float(1000000000)
    for idx, val in enumerate(coeff_1d_array):
        val = val.strip()
        error_col_index = idx + 1
        try:
            rounded_coeff_val = round(val)
        except:
            raise ValidationError(
                _('File: %(filename)s, Calibration Name: %(cal_name)s, Row: %(row)s, Column: %(column)s, %(value)s is an invalid Number. Please enter a valid Number (Digits + 1 optional decimal point, commas to separate multiple values).'),
                params={'row': error_row_index, 'value': val, 'column': error_col_index, 'filename': filename, 'cal_name': cal_name},
            )
        else:
            coeff_dec_places = rounded_coeff_val[::-1].find('.')
            try:
                assert coeff_dec_places <= valset_inst.cal_dec_places
            except:
                raise ValidationError(
                    _('File: %(filename)s, Calibration Name: %(cal_name)s, Row: %(row)s, Column: %(column)s, %(value)s Exceeded Instrument %(dec_places)s-digit decimal place maximum.'),
                    params={'row': error_row_index, 'dec_places': valset_inst.cal_dec_places, 'value': val, 'column': error_col_index, 'filename': filename, 'cal_name': cal_name},
                )
            else:
                try:
                    digits_only = rounded_coeff_val.replace('-','').replace('.','')
                    assert len(digits_only) <= 32
                except:
                    raise ValidationError(
                        _('File: %(filename)s, Calibration Name: %(cal_name)s, Row: %(row)s, Column: %(column)s, %(value)s Exceeded 32-digit max length'),
                        params={'row': error_row_index, 'column': error_col_index, 'value': val, 'filename': filename, 'cal_name': cal_name},
                    )
                else:
                    try:
                        std_val = round(val, format = 'std', output_type = float)
                        assert low <= std_val <= high
                    except:
                        raise ValidationError(
                            _('File: %(filename)s, Calibration Name: %(cal_name)s, Row: %(row)s, Column: %(column)s, %(value)s Coefficient value falls outside of threshold (%(low)s,%(high)s)'),
                            params={'row': error_row_index, 'column': error_col_index, 'value': val, 'filename': filename, 'cal_name': cal_name, 'low': low, 'high': high},
                        )
                    else:
                        continue


# Validator for Coefficient values within a CoefficientValueSet
# Checks for numeric-type, part-based decimal place limit, number of digits limit
# Displays array index/value of invalid input
def validate_coeff_vals(valset_inst, set_type, coeff_val_set, filename = '', cal_name = '', threshold = None):
    if set_type == 'sl':
        try:
            coeff_batch = coeff_val_set.split(',')
            assert len(coeff_batch) == 1
        except:
            raise ValidationError(
                _('More than 1 value associated with Single input type')
            )
        else:
            validate_coeff_array(coeff_batch, valset_inst, 0, filename, cal_name, threshold)
            return coeff_val_set

    elif set_type == '1d':
        try:
            coeff_batch = coeff_val_set.split(',')
        except:
            raise ValidationError(
                _('Unable to parse 1D array')
            )
        else:
            validate_coeff_array(coeff_batch, valset_inst, 0, filename, cal_name, threshold)
            return coeff_val_set

    elif set_type == '2d':
        try:
            coeff_2d_array = coeff_val_set.splitlines()
        except:
            raise ValidationError(
                _('Unable to parse 2D array')
            )
        else:
            for row_index, row_set in enumerate(coeff_2d_array):
                coeff_1d_array = row_set.split(',')
                validate_coeff_array(coeff_1d_array, valset_inst, row_index, filename, cal_name, threshold)
    return coeff_val_set


# Parses Coefficient Value notation
def find_notation(val):
    notation = 'std'
    val = val.lower()
    if ( 'e' in val ):
        notation = 'sci'
    return notation


# Parses Coefficient Value significant digits
def find_sigfigs(val):
    stripped_val = val.lower().replace('.','').replace('-','').strip('0')
    val_e_split = stripped_val.split('e')[0]
    sig_count = len(val_e_split)
    return sig_count



# Generate array of Coefficient Value instances to bulk upload into the DB
def parse_coeff_1d_array(coeff_1d_array, value_set_instance, row_index = 0):
    coeff_batch = []
    for idx, val in enumerate(coeff_1d_array):
        val = val.strip()
        notation = find_notation(val)
        sigfig = find_sigfigs(val)
        coeff_val_obj = CoefficientValue(
            coeff_value_set = value_set_instance,
            value = val,
            original_value = val,
            notation_format = notation,
            sigfig = sigfig,
            row = row_index
        )
        coeff_batch.append(coeff_val_obj)

    return coeff_batch


# Creates Coefficient value model instances for a valid CoefficientValueSet
def parse_valid_coeff_vals(value_set_instance):
    set_type = value_set_instance.coefficient_name.value_set_type
    coeff_vals = CoefficientValue.objects.filter(coeff_value_set = value_set_instance)
    coeff_batch = []
    if coeff_vals:
        coeff_vals.delete()
    if set_type  == 'sl' or set_type  == '1d':
        coeff_1d_array = value_set_instance.value_set.split(',')
        coeff_batch = parse_coeff_1d_array(coeff_1d_array, value_set_instance)
        CoefficientValue.objects.bulk_create(coeff_batch)
    elif set_type == '2d':
        val_array = []
        coeff_2d_array = value_set_instance.value_set.splitlines()
        for val_set_index, val_set in enumerate(coeff_2d_array):
            coeff_1d_array = val_set.split(',')
            parsed_batch = parse_coeff_1d_array(coeff_1d_array, value_set_instance, val_set_index)
            val_array.extend(parsed_batch)
        CoefficientValue.objects.bulk_create(val_array)
    return value_set_instance


# Copy all CoefficientNames across Parts
def copy_calibrations(to_id, from_id):
    to_part = Part.objects.get(id=to_id)
    from_part = Part.objects.get(id=from_id)
    if from_part.coefficient_name_events.exists():
        from_coeff_event = from_part.coefficient_name_events.first()
        to_coeff_event = to_part.coefficient_name_events.first()
        for name in from_coeff_event.coefficient_names.all():
            CoefficientName.objects.create(
                calibration_name = name.calibration_name,
                value_set_type = name.value_set_type,
                sigfig_override = name.sigfig_override,
                part = to_part,
                coeff_name_event=to_coeff_event,
            )

# Validator for Part Calibration Copy
# When a Part is selected, from which to copy Calibration Names into another Part, the function checks if duplicate Names exist between the two Parts in question.
def validate_part_select(to_part, from_part):
    if to_part.coefficient_name_events.exists():
        to_names = [name.calibration_name for name in to_part.coefficient_name_events.first().coefficient_names.all()]
    else:
        to_names = []
    if from_part.coefficient_name_events.exists():
        from_names = [name.calibration_name for name in from_part.coefficient_name_events.first().coefficient_names.all()]
    else:
        from_names = []
    try:
        assert not any(from_name in to_names for from_name in from_names)
    except:
        raise ValidationError(
            _('Duplicate Calibration Names exist between Parts. Please select Part with unique Calibration Names.')
        )
    else:
        pass
