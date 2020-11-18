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
from pprint import pprint

from django import forms
from django.shortcuts import get_object_or_404
from django.forms.models import inlineformset_factory
from django.core.exceptions import ValidationError

from django_summernote.widgets import SummernoteWidget
from bootstrap_datepicker_plus import DatePickerInput, DateTimePickerInput

from .models import Assembly, AssemblyPart, AssemblyType, AssemblyRevision, AssemblyDocument
# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels
labels = set_app_labels()


class AssemblyForm(forms.ModelForm):
    revision_code = forms.CharField(strip=True, initial='A',
        help_text='Enter a Revision Code for the initial version of this Assembly. Defaults to "A"',
    )

    class Meta:
        model = Assembly
        fields = ['name', 'assembly_type', 'assembly_number', 'description', 'revision_code' ]
        labels = {
            'name': '%s Name' % (labels['label_assemblies_app_singular']),
            'assembly_type': '%s Type' % (labels['label_assemblies_app_singular']),
            'assembly_number': '%s ID Number' % (labels['label_assemblies_app_singular']),
        }
        widgets = {
            'description': SummernoteWidget(),
        }

    def __init__(self, *args, **kwargs):

        if 'assembly_to_copy_pk' in kwargs:
            self.assembly_to_copy_pk = kwargs.pop('assembly_to_copy_pk')
        else:
            self.assembly_to_copy_pk = None
        super(AssemblyForm, self).__init__(*args, **kwargs)
        self.fields['assembly_type'].required = True

        if self.instance.pk:
            del self.fields['revision_code']


class AssemblyRevisionForm(forms.ModelForm):

    class Meta:
        model = AssemblyRevision
        fields = ['revision_code', 'created_at', 'revision_note', 'assembly']
        labels = {
            'created_at': 'Release Date',
            'note': 'Revision Notes',
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
            'revision_note': SummernoteWidget(),
            'assembly': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):

        if 'assembly_revision_pk' in kwargs:
            self.assembly_revision_pk = kwargs.pop('assembly_revision_pk')
        else:
            self.assembly_revision_pk = None
        super(AssemblyRevisionForm, self).__init__(*args, **kwargs)

    def clean_revision_code(self):
        # Need to check if the Revision Code is already in use on this Assembly
        revision_code = self.cleaned_data['revision_code']
        try:
            previous_revision = AssemblyRevision.objects.get(id=self.assembly_revision_pk)
            revisions = AssemblyRevision.objects.filter(assembly=previous_revision.assembly)

            for revision in revisions:
                if revision.revision_code == revision_code:
                    raise ValidationError('Revision Code already in use on this Assembly. Choose unique code.')
        except:
            pass

        return revision_code


AssemblyRevisionFormset = inlineformset_factory(Assembly, AssemblyRevision, form=AssemblyRevisionForm,
                                                fields=('revision_code', 'revision_note'),
                                                        widgets={
                                                            'revision_note': SummernoteWidget(),
                                                        }, extra=1, can_delete=False)
AssemblyDocumentationFormset = inlineformset_factory(AssemblyRevision, AssemblyDocument, fields=('name', 'doc_type', 'doc_link'), extra=1, can_delete=True)


class AssemblyPartForm(forms.ModelForm):

    class Meta:
        model = AssemblyPart
        fields = ['assembly_revision', 'part', 'parent', 'note']
        labels = {
            'part': 'Select Part Template',
            'parent': 'Parent %s Part' % (labels['label_assemblies_app_singular']),
            'note': 'Design Notes'
        }

        widgets = {
            'assembly_revision': forms.HiddenInput(),
        }

    class Media:
        js = ('js/form-assemblyparts.js',)

    def __init__(self, *args, **kwargs):

        if 'assembly_revision_pk' in kwargs:
            self.assembly_revision_pk = kwargs.pop('assembly_revision_pk')
        else:
            self.assembly_revision_pk = None

        if 'parent_pk' in kwargs:
            self.parent_pk = kwargs.pop('parent_pk')
        else:
            self.parent_pk = None

        super(AssemblyPartForm, self).__init__(*args, **kwargs)
        #self.fields['parent'].queryset = MooringPart.objects.none()
        #self.fields['parent'].queryset = AssemblyPart.objects.filter(id=self.parent_pk)
        if self.assembly_revision_pk:
            self.fields['parent'].queryset = AssemblyPart.objects.filter(assembly_revision_id=self.assembly_revision_pk)
        elif self.instance.pk:
            self.fields['parent'].queryset = AssemblyPart.objects.filter(assembly_revision=self.instance.assembly_revision)


class AssemblyTypeForm(forms.ModelForm):

    class Meta:
        model = AssemblyType
        fields = ['name' ]
        labels = {
            'name': '%s Type Name' % (labels['label_assemblies_app_singular']),
        }


"""
Custom Deletion form for AssemblyType
User needs to be able to choose a new AssemblyType for existing Assemblies or they
disappear from tree nav
"""
class AssemblyTypeDeleteForm(forms.Form):
    new_assembly_type = forms.ModelChoiceField(label='Select new Assembly Type', queryset=AssemblyType.objects.all())

    def __init__(self, *args, **kwargs):
        assembly_type_pk= kwargs.pop('pk')
        assembly_type_to_delete = get_object_or_404(AssemblyType, id=assembly_type_pk)

        super(AssemblyTypeDeleteForm, self).__init__(*args, **kwargs)
        # Check if this PartType has IPart Templates, remove new field if false
        if not assembly_type_to_delete.assemblies.exists():
            self.fields['new_assembly_type'].required = False
            self.fields['new_assembly_type'].widget = forms.HiddenInput()
