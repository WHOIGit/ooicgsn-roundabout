"""
# Copyright (C) 2019-2020 Woods Hole Oceanographic Institution
#
# This file is part of the Roundabout Database project ("RDB" or
# "ooicgsn-roundabout").
#
# ooicgsn-roundabout is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# ooicgsn-roundabout is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ooicgsn-roundabout in the COPYING.md file at the project root.
# If not, see <http://www.gnu.org/licenses/>.
"""

import datetime
import re

from django import forms
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory
from django.template.defaultfilters import slugify
from django_summernote.widgets import SummernoteWidget
from bootstrap_datepicker_plus import DatePickerInput, DateTimePickerInput
from mptt.forms import TreeNodeChoiceField

from .models import Part, PartType, Documentation, Revision
from roundabout.locations.models import Location
from roundabout.parts.widgets import PartParentWidget, PartLocationWidget
from roundabout.userdefinedfields.models import Field, FieldValue
from roundabout.calibrations.models import CoefficientName
from roundabout.calibrations.forms import CoefficientNameForm
from roundabout.inventory.models import Inventory
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PartForm(forms.ModelForm):

    part_number = forms.CharField(strip=True, help_text='Suggested format is ####-#####-#####', )

    class Meta:
        model = Part
        fields = ['part_number', 'name', 'friendly_name', 'part_type', 'cal_dec_places']
        labels = {
            'parent': 'Parent Assembly',
            'note': 'Part Template Notes',
            'cal_dec_places': 'Max Calibration Coefficient decimal places'
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


class PartUdfAddFieldForm(forms.ModelForm):

    class Meta:
        model = Part
        fields = ['user_defined_fields']
        labels = {
            'user_defined_fields': 'Select an existing Custom Field',
        }

        widgets = {
            'user_defined_fields': forms.CheckboxSelectMultiple()
        }


class PartUdfFieldSetValueForm(forms.Form):

    def __init__(self, *args, **kwargs):
        if 'pk' in kwargs:
            self.pk = kwargs.pop('pk')
        else:
            self.pk = None

        if 'field_pk' in kwargs:
            self.field_pk = kwargs.pop('field_pk')
        else:
            self.field_pk = None

        super(PartUdfFieldSetValueForm, self).__init__(*args, **kwargs)
        part = Part.objects.get(id=self.pk)
        field = Field.objects.get(id=self.field_pk)
        partfieldvalues = part.fieldvalues.filter(field=field)

        if field.field_type == 'IntegerField':
            self.fields['field_value'] = forms.IntegerField(label=str(field.field_name), required=False,
                                                help_text=str(field.field_description))
        elif field.field_type == 'DecimalField':
            self.fields['field_value'] = forms.DecimalField(label=str(field.field_name), required=False,
                                                help_text=str(field.field_description))
        elif field.field_type == 'DateField':
            self.fields['field_value'] = forms.DateTimeField(label=str(field.field_name), required=False,
                                                help_text=str(field.field_description),
                                                widget=DateTimePickerInput(
                                                    options={
                                                        "format": "YYYY-MM-DD hh:mm:ss", # moment date-time format
                                                        "showClose": True,
                                                        "showClear": True,
                                                        "showTodayButton": True,
                                                    }
                                                ))
        elif field.field_type == 'BooleanField':
            self.fields['field_value'] = forms.BooleanField(label=str(field.field_name), required=False,
                                                help_text=str(field.field_description))
        else:
            self.fields['field_value'] = forms.CharField(label=str(field.field_name), required=False,
                                                help_text=str(field.field_description))

        if partfieldvalues:
            for fieldvalue in partfieldvalues:
                self.fields['field_value'].initial = fieldvalue.field_value


class PartTypeForm(forms.ModelForm):

    class Meta:
        model = PartType
        fields = ['name', 'parent', 'ccc_toggle' ]
        labels = {
            'name': 'Part Type Name',
            'ccc_toggle': 'Enable Configs, Constants, and Calibration Coefficients'
        }


"""
Custom Deletion form for PartType
User needs to be able to choose a new PartType for existing Part Templates or they
disappear from tree nav
"""
class PartTypeDeleteForm(forms.Form):
    new_part_type = TreeNodeChoiceField(label='Select new Part Type', queryset=PartType.objects.all())

    def __init__(self, *args, **kwargs):
        part_type_pk= kwargs.pop('pk')
        part_type_to_delete = get_object_or_404(PartType, id=part_type_pk)

        super(PartTypeDeleteForm, self).__init__(*args, **kwargs)
        # Check if this PartType has IPart Templates, remove new field if false
        if not part_type_to_delete.parts.exists():
            self.fields['new_part_type'].required = False
            self.fields['new_part_type'].widget = forms.HiddenInput()
