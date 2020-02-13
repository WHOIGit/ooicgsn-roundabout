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

from django import forms
from django.forms.models import inlineformset_factory

from .models import Assembly, AssemblyPart, AssemblyType

# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels
labels = set_app_labels()


class AssemblyForm(forms.ModelForm):

    class Meta:
        model = Assembly
        fields = ['name', 'assembly_type', 'assembly_number', 'description', ]
        labels = {
            'name': 'Assembly Name',
            'assembly_number': 'Assembly ID Number',
        }

    def __init__(self, *args, **kwargs):

        if 'pk' in kwargs:
            self.pk = kwargs.pop('pk')
        else:
            self.pk = None

        super(AssemblyForm, self).__init__(*args, **kwargs)


class AssemblyPartForm(forms.ModelForm):

    class Meta:
        model = AssemblyPart
        fields = ['assembly', 'part', 'parent', 'note']
        labels = {
            'part': 'Select Part Template',
            'parent': 'Parent Assembly',
            'note': 'Design Notes'
        }

        widgets = {
            'assembly': forms.HiddenInput(),
        }

    class Media:
        js = ('js/form-assemblyparts.js',)

    def __init__(self, *args, **kwargs):

        if 'assembly_pk' in kwargs:
            self.assembly_pk = kwargs.pop('assembly_pk')
        else:
            self.assembly_pk = None

        if 'parent_pk' in kwargs:
            self.parent_pk = kwargs.pop('parent_pk')
        else:
            self.parent_pk = None

        super(AssemblyPartForm, self).__init__(*args, **kwargs)
        #self.fields['parent'].queryset = MooringPart.objects.none()
        #self.fields['parent'].queryset = AssemblyPart.objects.filter(id=self.parent_pk)
        if self.assembly_pk:
            self.fields['parent'].queryset = AssemblyPart.objects.filter(assembly_id=self.assembly_pk)
        elif self.instance.pk:
            self.fields['parent'].queryset = AssemblyPart.objects.filter(assembly=self.instance.assembly)


class AssemblyTypeForm(forms.ModelForm):

    class Meta:
        model = AssemblyType
        fields = ['name' ]
        labels = {
        'name': 'Assembly Type Name'
    }
