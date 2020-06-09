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
class CalibrationEventForm(forms.ModelForm):
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
        if self.has_changed():
            if commit:
                value_set.save()
                parse_valid_coeff_vals(value_set)
                return value_set


# CalibrationName Form
# Inputs: Name, Input Type, Significant Figures
class CoefficientNameForm(forms.ModelForm):
    class Meta:
        model = CoefficientName
        fields = ['calibration_name', 'value_set_type', 'sigfig_override']
        labels = {
            'calibration_name': 'Name',
            'value_set_type': 'Type',
            'sigfig_override': 'Significant Figures'
        }

    def clean_sigfig_override(self):
        raw_sigfig = self.cleaned_data.get('sigfig_override')
        try:
            assert 0 <= raw_sigfig <= 20
        except:
            raise ValidationError(
                    _('Input must be between 0 and 20.')
                )
        else:
            return raw_sigfig


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

# Coefficient ValueSet form instance generator for CalibrationEvents
EventValueSetFormset = inlineformset_factory(
    CalibrationEvent, 
    CoefficientValueSet, 
    form=CoefficientValueSetForm,
    fields=('coefficient_name', 'value_set', 'notes'), 
    extra=1, 
    can_delete=True
)

# Coefficient Name form instance generator for Parts
PartCalNameFormset = inlineformset_factory(
    Part, 
    CoefficientName, 
    form=CoefficientNameForm, 
    fields=('calibration_name', 'value_set_type', 'sigfig_override'), 
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
def validate_coeff_array(coeff_1d_array, valset_inst, val_set_index = 0):
    error_row_index = val_set_index + 1
    for idx, val in enumerate(coeff_1d_array):
        val = val.strip()
        error_col_index = idx + 1
        try:
            rounded_coeff_val = round(val)
        except:
            raise ValidationError(
                _('Row: %(row)s, Column: %(column)s, %(value)s is an invalid Number. Please enter a valid Number (Digits + 1 optional decimal point).'),
                params={'row': error_row_index, 'value': val, 'column': error_col_index},
            )
        else:
            coeff_dec_places = rounded_coeff_val[::-1].find('.')
            try:
                assert coeff_dec_places <= valset_inst.cal_dec_places
            except:
                raise ValidationError(
                    _('Row: %(row)s, Column: %(column)s, %(value)s Exceeded Instrument %(dec_places)s-digit decimal place maximum.'),
                    params={'row': error_row_index, 'dec_places': valset_inst.cal_dec_places, 'value': val, 'column': error_col_index},
                )
            else:
                try:
                    assert len(rounded_coeff_val) <= 21
                except:
                    raise ValidationError(
                        _('Row: %(row)s, Column: %(column)s, %(value)s Exceeded 20-digit max length'),
                        params={'row': error_row_index, 'column': error_col_index, 'value': val},
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
            CoefficientValue.objects.bulk_create(parsed_batch)
    return value_set_instance

