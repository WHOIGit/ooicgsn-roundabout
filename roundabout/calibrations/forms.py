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

# Validates Single-value Coefficients
# Checks for single-length, numeric-type, part-based decimal places, number of digits
def clean_single_coeff(val, part_dec_places):
    try:
        split_set = val.split(',')
        assert len(split_set) == 1
    except:
        raise ValidationError(
            _('More than 1 value associated with element')
        )
    else:   
        try:
            rounded_coeff_val = round(split_set[0])
        except:
            raise ValidationError(
                _('%(value)s is an invalid Number. Please enter a valid Number (Digits + 1 optional decimal point).'),
                params={'value': split_set[0]},
            )
        else:
            coeff_dec_places = rounded_coeff_val[::-1].find('.')
            try:
                assert coeff_dec_places <= part_dec_places
            except:
                raise ValidationError(
                    _('Exceeded Instrument %(dec_places)s-digit decimal place maximum.'),
                    params={'dec_places': part_dec_places},
                )
            else:
                try:
                    assert len(rounded_coeff_val) <= 21
                except:
                    raise ValidationError(
                        _('Exceeded 20-digit max length')
                    )
                else:
                    return val


# Validates 1-Dimensional, comma-separated arrays of Coefficients
# Checks for numeric-type, part-based decimal place limit, number of digits limit
# Displays array index/value of invalid input
def clean_1d_coeffs(vals, part_dec_places):
    split_set = vals.split(',')
    for idx, val in enumerate(split_set):
        
        val = val.strip()
        try:
            rounded_coeff_val = round(val)
        except:
            raise ValidationError(
                _('Index %(index)s: %(value)s is an invalid Number. Please enter a valid Number (Digits + 1 optional decimal point).'),
                params={'value': val, 'index': idx},
            )
        else:
            coeff_dec_places = rounded_coeff_val[::-1].find('.')
            try:
                assert coeff_dec_places <= part_dec_places
            except:
                raise ValidationError(
                    _('Index %(index)s: Exceeded Instrument %(dec_places)s-digit decimal place maximum.'),
                    params={'dec_places': part_dec_places, 'index': idx},
                )
            else:
                try:
                    assert len(rounded_coeff_val) <= 21
                except:
                    raise ValidationError(
                        _('Index %(index)s: Exceeded 20-digit max length'),
                        params={'index': idx},
                    )
                else:
                    # get_or_create
                    # coeffModel.objects.create()
                    continue
    return vals



# Coefficient form
# Inputs: Coefficient values and notes per Part Calibration 
class CoefficientValueForm(forms.ModelForm):
    class Meta:
        model = CoefficientValueSet
        fields = ['coefficient_name','value_set', 'notes']
        labels = {
            'coefficient_name': 'Calibration Name',
            'value_set': 'Calibration Coefficient(s)',
            'notes': 'Additional Notes'
        }

    def clean_value_set(self):
        raw_set = self.cleaned_data.get('value_set')
        coefficient_name = self.cleaned_data.get('coefficient_name')
        try:
            cal_obj = CoefficientName.objects.get(part = self.instance.part, calibration_name = coefficient_name)
        except:
            raise ValidationError(
                _('Unable to query selected Calibration instance'),
            )
        if cal_obj:
            set_type =  cal_obj.value_set_type
        else:
            set_type = 'None'
        part_dec_places = self.instance.cal_dec_places
        if set_type == 'sl':
            return clean_single_coeff(raw_set, part_dec_places)
        elif set_type == '1d':
            return clean_1d_coeffs(raw_set, part_dec_places)
        else:
            raise ValidationError(
                _('Undefined set type'),
            )

    def __init__(self, *args, **kwargs):
        if 'inv_id' in kwargs:
            self.inv_id = kwargs.pop('inv_id')
        super(CoefficientValueForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'inv_id'):
            inv_inst = Inventory.objects.get(id = self.inv_id)
            self.fields['coefficient_name'].queryset = CoefficientName.objects.filter(part = inv_inst.part).order_by('created_at')
            self.instance.cal_dec_places = inv_inst.part.cal_dec_places
            self.instance.part = inv_inst.part

# Coefficient form instance generator
CoefficientFormset = inlineformset_factory(
    CalibrationEvent, 
    CoefficientValueSet, 
    form=CoefficientValueForm,
    fields=('coefficient_name', 'value_set', 'notes'), 
    extra=1, 
    can_delete=True
    )
