from django import forms
from .models import CoefficientName, CoefficientValue, CalibrationEvent
from django.forms.models import inlineformset_factory

class CalibrationAddForm(forms.ModelForm):

    class Meta:
        model = CalibrationEvent 
        fields = ['calibration_date', 'approved']
        labels = {
            'calibration_date': 'Calibration Date',
            'approved': 'Approved'
        }
        widgets = {
            'calibration_date': forms.DateInput(),
        }

CoefficientFormset = inlineformset_factory(
    CalibrationEvent, 
    CoefficientValue, 
    fields=('coefficient_name','value','notes',), 
    extra=1, 
    can_delete=True
    )