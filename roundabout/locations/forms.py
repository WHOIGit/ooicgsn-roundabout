from django import forms
from django.forms.models import inlineformset_factory
from django.contrib.sites.models import Site

from .models import Location



class LocationForm(forms.ModelForm):

    class Meta:
        model = Location
        fields = ['name', 'parent', 'location_type', 'location_id' ]
        labels = {
        'location_id': 'Location ID'
    }

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)

        # Default Location Types
        LOC_TYPES = (
            ('', ''),
            ('Array', 'Array'),
            ('Mooring', 'Mooring'),
        )

        # Custom Location Types for OBS
        LOC_TYPES_OBS = (
            ('', ''),
            ('Instrument', 'Instrument'),
        )

        current_site = Site.objects.get_current()

        if current_site.domain == 'obs-rdb.whoi.edu':
            self.fields['location_type'].choices = LOC_TYPES_OBS
        else:
            self.fields['location_type'].choices = LOC_TYPES
