from django import forms
from django.forms.models import inlineformset_factory

from .models import Location


class LocationForm(forms.ModelForm):

    class Meta:
        model = Location
        fields = ['name', 'parent', 'location_type', 'location_id' ]
        labels = {
        'location_id': 'Location ID'
    }
