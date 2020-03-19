from django import forms
from .models import CoefficientName, CoefficientValue, CalibrationEvent
from django.forms.models import inlineformset_factory

class CalibrationAddForm(forms.ModelForm):

    class Meta:
        model = CoefficientValue
        fields = ['coefficient_name', 'value', 'notes']
        labels = {
            'coefficient_name': 'Name',
            'value': 'Value',
            'notes': 'Notes'
        }

CoefficientFormset = inlineformset_factory(CalibrationEvent, CoefficientValue, fields=('value','notes',), extra=1, can_delete=True)