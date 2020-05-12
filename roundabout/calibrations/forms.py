from django import forms
from .models import CoefficientName, CoefficientValue, CalibrationEvent
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

# Coefficient form
# Inputs: Coefficient values and notes per Part Calibration 
class CoefficientValueForm(forms.ModelForm):
    class Meta:
        model = CoefficientValue
        fields = ['coefficient_name', 'value', 'notation_format']
        labels = {
            'coefficient_name': 'Calibration Name',
            'value': 'Calibration Coefficient',
            'notation_format': 'Notation Format'
        }

    def clean_value(self):
        raw_coeff_val = self.cleaned_data.get('value')
        part_dec_places = self.instance.cal_dec_places
        try:
            rounded_coeff_val = round(raw_coeff_val)
            print(rounded_coeff_val)
        except:
            raise ValidationError(
                _('%(value)s is an invalid Number. Please enter a valid Number (Digits + 1 optional decimal point).'),
                params={'value': raw_coeff_val},
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
                        _('Exceed global maximum number of digits'),
                    )
                else:
                    return raw_coeff_val

    def __init__(self, *args, **kwargs):
        if 'inv_id' in kwargs:
            self.inv_id = kwargs.pop('inv_id')
        super(CoefficientValueForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'inv_id'):
            inv_inst = Inventory.objects.get(id = self.inv_id)
            self.fields['coefficient_name'].queryset = CoefficientName.objects.filter(part = inv_inst.part)
            self.instance.cal_dec_places = inv_inst.part.cal_dec_places

# Coefficient form instance generator
CoefficientFormset = inlineformset_factory(
    CalibrationEvent, 
    CoefficientValue, 
    form=CoefficientValueForm,
    fields=('coefficient_name', 'value', 'notation_format'), 
    extra=1, 
    can_delete=True
    )
