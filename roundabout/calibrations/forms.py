from django import forms
from .models import CoefficientName

class CalibrationAddForm(forms.ModelForm):

    class Meta:
        model = CoefficientName
        fields = ['calibration_name']
        labels = {
            'calibration_name': 'Name'
        }