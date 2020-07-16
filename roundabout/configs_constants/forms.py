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
from .models import ConfigEvent, ConfigName, ConfigValue
from roundabout.inventory.models import Inventory, Deployment
from roundabout.parts.models import Part
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from bootstrap_datepicker_plus import DatePickerInput
from sigfig import round
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


TEST_DEPLOYMENT_DATES = (
      ("02/23/2015", "02/23/2015"),
      ("07/24/2013", "07/24/2013"),
      ("07/01/2016", "07/01/2016"),
  )

# Configuration Event form 
# Inputs: Config Date and Approval
class ConfigEventForm(forms.ModelForm):
    class Meta:
        model = ConfigEvent 
        fields = ['deployment','approved']
        labels = {
            'deployment': 'Deployment',
            'approved': 'Approved'
        }
        widgets = {
            'deployment': forms.Select(
                attrs = {
                    'required': True
                }
            )
        }
    def __init__(self, *args, **kwargs):
        super(ConfigEventForm, self).__init__(*args, **kwargs)

# Configuration Value form
# Inputs: Configuration values and notes per Part Config Type
class ConfigValueForm(forms.ModelForm):
    class Meta:
        model = ConfigValue
        fields = ['config_name','config_value', 'notes']
        labels = {
            'config_name': 'Configuration/Constant Name',
            'config_value': 'Value',
            'notes': 'Additional Notes'
        }
        widgets = {
            'config_value': forms.Textarea(
                attrs = {
                    'style': 'white-space: nowrap'
                }
            )
        }
    
    def __init__(self, *args, **kwargs):
        super(ConfigValueForm, self).__init__(*args, **kwargs)

    def clean_config_name(self):
        config_name = self.cleaned_data.get('config_name')
        return config_name

# Configuration Name Form
# Inputs: Name, Input Type
class ConfigNameForm(forms.ModelForm):
    class Meta:
        model = ConfigName
        fields = ['name', 'config_type']
        labels = {
            'name': 'Configuration/Constant Name',
            'config_type': 'Type'
        }
        widgets = {
            'name': forms.TextInput(
                attrs = {
                    'required': False
                }
            ),
        }
        
# Configuration Value form instance generator for ConfigEvents
ConfigEventValueFormset = inlineformset_factory(
    ConfigEvent, 
    ConfigValue, 
    form=ConfigValueForm,
    fields=('config_name', 'config_value', 'notes'), 
    extra=1, 
    can_delete=True
)

# Configuration Name form instance generator for Parts
PartConfigNameFormset = inlineformset_factory(
    Part, 
    ConfigName, 
    form=ConfigNameForm, 
    fields=('name', 'config_type'), 
    extra=1, 
    can_delete=True
)