from django import forms
from .models import Calibration

class CalibrationAddForm(forms.ModelForm):

    class Meta:
        model = Calibration
        fields = ['name']
        labels = {
            'name': 'Name'
        }