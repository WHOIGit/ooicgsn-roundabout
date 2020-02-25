from django import forms
from .models import Calibration

class CalibrationAddForm(forms.ModelForm):

    class Meta:
        model = Calibration
        fields = ['name', 'coefficient']
        labels = {
            'name': 'Name',
            'coefficient': 'Coefficient Value',
        }