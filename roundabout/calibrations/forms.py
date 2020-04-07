from django import forms
from .models import CoefficientName, CoefficientValue, CalibrationEvent
from roundabout.inventory.models import Inventory
from roundabout.parts.models import Part
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from bootstrap_datepicker_plus import DatePickerInput

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


class CoefficientValueForm(forms.ModelForm):
    class Meta:
        model = CoefficientValue
        fields = ['coefficient_name','value','notes']
    def __init__(self, *args, **kwargs):
        if 'inv_id' in kwargs:
            self.inv_id = kwargs.pop('inv_id')
        super(CoefficientValueForm, self).__init__(*args, **kwargs)
        if hasattr(self,'inv_id'):
            inv_inst = Inventory.objects.get(id=self.inv_id)
            self.fields['coefficient_name'].queryset = CoefficientName.objects.filter(part=inv_inst.part)


CoefficientFormset = inlineformset_factory(
    CalibrationEvent, 
    CoefficientValue, 
    form=CoefficientValueForm,
    fields=('coefficient_name','value','notes',), 
    extra=1, 
    can_delete=True
    )
