from django import forms
from mptt.forms import TreeNodeChoiceField

from .models import MooringPart
from common.util.validators import validate_trim_whitespace
from roundabout.locations.models import Location


class MooringForm(forms.ModelForm):

    class Meta:
        model = MooringPart
        fields = ['part', 'location', 'parent', 'note']
        labels = {
            'part': 'Select Part Template',
            'parent': 'Parent Assembly',
            'note': 'Design Notes'
        }

    class Media:
        js = ('js/form-moorings.js',)

    def __init__(self, *args, **kwargs):

        if 'parent_pk' in kwargs:
            self.parent = kwargs.pop('parent_pk')
        else:
            self.parent = None

        if 'current_location' in kwargs:
            self.current_location = kwargs.pop('current_location')
        else:
            self.current_location = None

        super(MooringForm, self).__init__(*args, **kwargs)
        #self.fields['parent'].queryset = MooringPart.objects.none()
        self.fields['location'].queryset = Location.objects.all()
        self.fields['parent'].queryset = MooringPart.objects.filter(id=self.parent)

        if 'location' in self.data:
            try:
                location_id = int(self.data.get('location'))
                self.fields['parent'].queryset = MooringPart.objects.filter(location_id=location_id)
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
        elif self.instance.pk:
            self.fields['parent'].queryset = MooringPart.objects.filter(location_id=self.instance.location.id)


class MooringCopyLocationForm(forms.Form):
    location = TreeNodeChoiceField(queryset = Location.objects.all(), label="Select New Location To Copy Mooring Template To" )

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk')
        super(MooringCopyLocationForm, self).__init__(*args, **kwargs)
        self.fields['location'].queryset = Location.objects.exclude(id=self.pk)

    def clean_location(self):
        data = self.cleaned_data['location']

        if data.mooring_parts.exists():
            msg = 'Location already has Mooring Template!'
            self.add_error('location', msg)

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return data
