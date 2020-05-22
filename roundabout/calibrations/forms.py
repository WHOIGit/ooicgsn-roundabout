from django import forms
from .models import CoefficientName, CoefficientValueSet, CalibrationEvent, CoefficientValue
from roundabout.inventory.models import Inventory
from roundabout.parts.models import Part
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from bootstrap_datepicker_plus import DatePickerInput
from sigfig import round
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Event form 
# Inputs: Effective Date and Approval
class CalibrationAddForm(forms.ModelForm):
    class Meta:
        model = CalibrationEvent 
        fields = ['calibration_date', 'approved']
        labels = {
            'calibration_date': 'Calibration Date',
            'approved': 'Approved'
        }
        widgets = {
            'calibration_date': DatePickerInput(
                options={
                    "format": "MM/DD/YYYY", # moment date-time format
                    "showClose": True,
                    "showClear": True,
                    "showTodayButton": True,
                }
            )
        }

# 
def validate_coeff_array(coeff_1d_array, valset_inst, val_set_index = 0):
    for idx, val in enumerate(coeff_1d_array):
        val = val.strip()
        try:
            rounded_coeff_val = round(val)
        except:
            raise ValidationError(
                _('Row: %(row)s, Column: %(column)s, %(value)s is an invalid Number. Please enter a valid Number (Digits + 1 optional decimal point).'),
                params={'row': val_set_index, 'value': val, 'column': idx},
            )
        else:
            coeff_dec_places = rounded_coeff_val[::-1].find('.')
            try:
                assert coeff_dec_places <= valset_inst.cal_dec_places
            except:
                raise ValidationError(
                    _('Row: %(row)s, Column: %(column)s, %(value)s Exceeded Instrument %(dec_places)s-digit decimal place maximum.'),
                    params={'row': val_set_index, 'dec_places': valset_inst.cal_dec_places, 'value': val, 'index': idx},
                )
            else:
                try:
                    assert len(rounded_coeff_val) <= 21
                except:
                    raise ValidationError(
                        _('Row: %(row)s, Column: %(column)s, %(value)s Exceeded 20-digit max length'),
                        params={'row': val_set_index, 'index': idx},
                    )
                else:
                    continue


# Validator for Coefficient values within a CoefficientValueSet
# Checks for numeric-type, part-based decimal place limit, number of digits limit
# Displays array index/value of invalid input
def validate_coeff_vals(valset_inst, set_type, coeff_val_set):  
    if set_type == 'sl':
        try:
            coeff_batch = coeff_val_set.split(',')
            assert len(coeff_batch) == 1
        except:
            raise ValidationError(
                _('More than 1 value associated with Single input type')
            )
        else:
            validate_coeff_array(coeff_batch, valset_inst)
            return coeff_val_set

    elif set_type == '1d':
        try:
            coeff_batch = coeff_val_set.split(',')
        except:
            raise ValidationError(
                _('Unable to parse 1D array')
            )
        else:
            validate_coeff_array(coeff_batch, valset_inst)
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
                validate_coeff_array(coeff_1d_array, valset_inst, row_index)
    return coeff_val_set


def parse_coeff_1d_array(coeff_1d_array, value_set_instance):
    coeff_batch = []
    for idx, val in enumerate(coeff_1d_array):
        val = val.strip()
        coeff_val_obj = CoefficientValue(
            coeff_value_set = value_set_instance, 
            value = val
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
    elif set_type == '2d':
        val_array = []
        coeff_2d_array = value_set_instance.value_set.splitlines()
        for val_set_index, val_set in enumerate(coeff_2d_array):
            coeff_1d_array = val_set.split(',')
            for val_index, val in enumerate(coeff_1d_array):
                val_array.append(val)
        coeff_batch = parse_coeff_1d_array(val_array, value_set_instance)
    CoefficientValue.objects.bulk_create(coeff_batch)
    return value_set_instance


# Coefficient form
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
            'value_set': forms.Textarea(
                attrs = {
                    'white-space': 'nowrap'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        if 'inv_id' in kwargs:
            self.inv_id = kwargs.pop('inv_id')
        super(CoefficientValueSetForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'inv_id'):
            inv_inst = Inventory.objects.get(id = self.inv_id)
            self.fields['coefficient_name'].queryset = CoefficientName.objects.filter(part = inv_inst.part).order_by('created_at')
            self.instance.cal_dec_places = inv_inst.part.cal_dec_places
            self.instance.part = inv_inst.part

    def clean_value_set(self):
        raw_set = self.cleaned_data.get('value_set')
        coefficient_name = self.cleaned_data.get('coefficient_name')
        try:
            cal_obj = CoefficientName.objects.get(part = self.instance.part, calibration_name = coefficient_name)
            set_type =  cal_obj.value_set_type
        except:
            raise ValidationError(
                _('Unable to query selected Calibration instance'),
            )
        else:
            return validate_coeff_vals(self.instance, set_type, raw_set)

    def save(self, commit = True): 
        value_set = super(CoefficientValueSetForm, self).save(commit = False)
        if commit:
            value_set.save()
            parse_valid_coeff_vals(value_set)
        return value_set

# Coefficient form instance generator
CoefficientFormset = inlineformset_factory(
    CalibrationEvent, 
    CoefficientValueSet, 
    form=CoefficientValueSetForm,
    fields=('coefficient_name', 'value_set', 'notes'), 
    extra=1, 
    can_delete=True
    )
