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
from django.db.models import Subquery

from .models import Tag
from roundabout.inventory.models import AssemblyPart
from roundabout.configs_constants.models import ConfigName, ConfigDefault


class TagForm(forms.ModelForm):

    class Meta:
        model = Tag
        fields = ['assembly_part', 'text', 'color', 'config_name']

    assembly_part = forms.ModelChoiceField(required=False,queryset=AssemblyPart.objects.all(), widget=forms.HiddenInput())
    config_name = forms.ModelChoiceField(required=False, queryset=ConfigName.objects.none(), label='Configuration Name/Value')

    def __init__(self, *args, **kwargs):
        super(TagForm, self).__init__(*args, **kwargs)

        # limit config_name field options to those available in the assembly part
        cde = self.initial['assembly_part'].assemblypart_configdefaultevents.last()
        config_defaults = ConfigDefault.objects.filter(conf_def_event=cde)
        self.fields['config_name'].queryset = ConfigName.objects.filter(
            config_defaults__in=Subquery(config_defaults.values('pk')), config_type='conf')



