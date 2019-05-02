import datetime
import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory
from django_summernote.widgets import SummernoteWidget
from bootstrap_datepicker_plus import DatePickerInput

from .models import Part, Documentation, Revision
from roundabout.locations.models import Location
from roundabout.parts.widgets import PartParentWidget, PartLocationWidget


class PartForm(forms.ModelForm):

    part_number = forms.CharField(strip=True, help_text='Suggested format is ####-#####-#####', )

    class Meta:
        model = Part
        fields = ['part_number', 'name', 'friendly_name', 'part_type', 'is_equipment']
        labels = {
            'parent': 'Parent Assembly',
            'is_equipment': 'Is this part considered equipment?',
            'note': 'Part Template Notes'
        }
"""
    def clean_part_number(self):
        part_number = self.cleaned_data['part_number']
        if not re.match(r'^[a-zA-Z0-9_]{4}-[a-zA-Z0-9_]{5}-[a-zA-Z0-9_]{5}$', part_number):
            part_number = part_number + '-00001'
        if not re.match(r'^[a-zA-Z0-9_]{4}-[a-zA-Z0-9_]{5}-[a-zA-Z0-9_]{5}$', part_number):
            raise ValidationError('Part Number in wrong format. Must be ####-#####-#####')
        return part_number
"""

RevisionFormset = inlineformset_factory(Part, Revision, fields=('revision_code', 'unit_cost', 'refurbishment_cost', 'note'), widgets={
        'note': SummernoteWidget(),
    }, extra=1, can_delete=False)
DocumentationFormset = inlineformset_factory(Revision, Documentation, fields=('name', 'doc_type', 'doc_link'), extra=1, can_delete=True)


class RevisionForm(forms.ModelForm):

    class Meta:
        model = Revision
        fields = ['revision_code', 'created_at', 'unit_cost', 'refurbishment_cost', 'note', 'part']
        labels = {
            'created_at': 'Release Date',
            'note': 'Revision Notes'
        }
        widgets = {
            'created_at': DatePickerInput(
                options={
                    "format": "MM/DD/YYYY", # moment date-time format
                    "showClose": True,
                    "showClear": True,
                    "showTodayButton": True,
                }
            ),
            'note': SummernoteWidget(),
            'part': forms.HiddenInput(),
        }


class PartSubassemblyAddForm(forms.ModelForm):

    class Meta:
        model = Part
        fields = ['name', 'revision', 'part_number' ]
        labels = {
        'parent': 'Parent Assembly'
    }

    def __init__(self, *args, **kwargs):
        super(PartSubassemblyAddForm, self).__init__(*args, **kwargs)
        self.fields['location'].queryset = Location.objects.filter(
            tree_id=2).filter(level__gt=0).prefetch_related('parts')


class PartSubassemblyEditForm(forms.ModelForm):

    class Meta:
        model = Part
        fields = ['name' ]
