import datetime
import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory
from django.template.defaultfilters import slugify
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


class PartCustomFieldForm(forms.Form):
    field_type_choices =[ ('CharField', 'Text Field'),
                          ('IntegerField', 'Integer Field'),
                          ('DecimalField', 'Decimal Field'),
                          ('DateField', 'Date Field'),
                          ('BooleanField', 'Boolean Field'),
                        ]

    field_name = forms.CharField(required=True)
    field_description = forms.CharField(required=False)
    field_type = forms.ChoiceField(choices = field_type_choices, required=True)
    field_default_value = forms.CharField(required=False)
    field_is_global = forms.TypedChoiceField(coerce=lambda x: x =='True', choices=((False, 'No'), (True, 'Yes')),
                                widget=forms.RadioSelect,
                                required=False,
                                label='Is this a global field value for this Part?',
                                help_text='Select "Yes" if this single field value applies to all Inventory items of this Part. \
                                            If "No", this field will be editable at the Inventory item level.')

    def __init__(self, *args, **kwargs):
        if 'pk' in kwargs:
            self.pk = kwargs.pop('pk')
        else:
            self.pk = None

        super(PartCustomFieldForm, self).__init__(*args, **kwargs)

    # Validation to check that the Field Name is unique for this part
    def clean_field_name(self):
        field_name = self.cleaned_data['field_name']
        field_id = slugify(field_name)
        part = Part.objects.get(id=self.pk)

        if part.custom_fields:
            fields = part.custom_fields['fields']
            for field in fields:
                if field['field_id'] == field_id:
                    raise ValidationError('Field Name already in use. Please pick a unique name.')

        return field_name


class PartCustomFieldUpdateForm(forms.Form):
    field_type_choices =[ ('CharField', 'Text Field'),
                          ('IntegerField', 'Integer Field'),
                          ('DecimalField', 'Decimal Field'),
                          ('DateField', 'Date Field'),
                          ('BooleanField', 'Boolean Field'),
                        ]

    field_name = forms.CharField(required=True)
    field_description = forms.CharField(required=False)
    field_type = forms.ChoiceField(choices = field_type_choices, required=True)
    field_default_value = forms.CharField(required=False)
    field_is_global = forms.TypedChoiceField(coerce=lambda x: x =='True', choices=((False, 'No'), (True, 'Yes')),
                                widget=forms.RadioSelect,
                                required=False,
                                label='Is this a global field value for this Part?',
                                help_text='Select "Yes" if this single field value applies to all Inventory items of this Part. \
                                            If "No", this field will be editable at the Inventory item level.')

    def __init__(self, *args, **kwargs):
        if 'pk' in kwargs:
            self.pk = kwargs.pop('pk')
        else:
            self.pk = None

        if 'field_id' in kwargs:
            self.field_id = kwargs.pop('field_id')
        else:
            self.field_id = None

        super(PartCustomFieldUpdateForm, self).__init__(*args, **kwargs)
        part = Part.objects.get(id=self.pk)

        if part.custom_fields:
            fields = part.custom_fields['fields']
            for field in fields:
                if field['field_id'] == self.field_id:
                    self.fields['field_name'].initial = field['field_name']
                    self.fields['field_description'].initial = field['field_description']
                    self.fields['field_type'].initial = field['field_type']
                    self.fields['field_default_value'].initial = field['field_default_value']
                    self.fields['field_is_global'].initial = field['field_is_global']


class PartCustomFieldDeleteForm(forms.Form):

    def __init__(self, *args, **kwargs):
        if 'pk' in kwargs:
            self.pk = kwargs.pop('pk')
        else:
            self.pk = None

        if 'field_id' in kwargs:
            self.field_id = kwargs.pop('field_id')
        else:
            self.field_id = None

        super(PartCustomFieldDeleteForm, self).__init__(*args, **kwargs)
