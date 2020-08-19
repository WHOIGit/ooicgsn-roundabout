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
from .models import ConfigEvent, ConfigName, ConfigValue, ConstDefault, ConstDefaultEvent, ConfigDefaultEvent, ConfigDefault, ConfigNameEvent
from roundabout.inventory.models import Inventory, Deployment
from roundabout.parts.models import Part
from roundabout.users.models import User
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from bootstrap_datepicker_plus import DatePickerInput
from sigfig import round
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _



# Configuration Event form 
# Inputs: Config Date and Approval
class ConfigEventForm(forms.ModelForm):
    class Meta:
        model = ConfigEvent 
        fields = ['deployment','user_draft']
        labels = {
            'deployment': 'Deployment',
            'user_draft': 'Reviewers'
        }
        widgets = {
            'deployment': forms.Select(
                attrs = {
                    'required': False
                }
            ),
            'user_draft': forms.SelectMultiple()
        }
    def __init__(self, *args, **kwargs):
        super(ConfigEventForm, self).__init__(*args, **kwargs)
        self.fields['user_draft'].queryset = User.objects.all().exclude(groups__name__in=['inventory only']).order_by('username')
        self.fields['deployment'].required = False

    def save(self, commit = True): 
        event = super(ConfigEventForm, self).save(commit = False)
        if commit:
            event.save()
            if event.user_approver.exists():
                for user in event.user_approver.all():
                    event.user_draft.add(user)
                    event.user_approver.remove(user)
            event.save()
            return event


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
            'config_name': forms.Select(
                attrs = {
                    'readonly': True,
                    'style': 'cursor: not-allowed; pointer-events: none; background-color: #d5dfed;'
                }
            ),
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

# ConfigNameEvent form 
# Inputs: Reviewers 
class ConfigNameEventForm(forms.ModelForm):
    class Meta:
        model = ConfigNameEvent 
        fields = ['user_draft']
        labels = {
            'user_draft': 'Reviewers'
        }
        widgets = {
            'user_draft': forms.SelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super(ConfigNameEventForm, self).__init__(*args, **kwargs)
        self.fields['user_draft'].queryset = User.objects.all().exclude(groups__name__in=['inventory only']).order_by('username')

    def clean_user_draft(self):
        user_draft = self.cleaned_data.get('user_draft')
        return user_draft

    def save(self, commit = True): 
        event = super(ConfigNameEventForm, self).save(commit = False)
        if commit:
            event.save()
            if event.user_approver.exists():
                for user in event.user_approver.all():
                    event.user_draft.add(user)
                    event.user_approver.remove(user)
            event.save()
            return event

# Configuration Name Form
# Inputs: Name, Input Type
class ConfigNameForm(forms.ModelForm):
    class Meta:
        model = ConfigName
        fields = [
            'name', 
            'config_type', 
            'include_with_calibrations'
        ] 
        labels = {
            'name': 'Configuration/Constant Name',
            'config_type': 'Type',
            'include_with_calibrations': 'Export with Calibrations' 
        }
        widgets = {
            'name': forms.TextInput(
                attrs = {
                    'required': False
                }
            ),
            'include_with_calibrations': forms.CheckboxInput() 
        }


# Constant Default form
# Inputs: Constant default values
class ConstDefaultForm(forms.ModelForm):
    class Meta:
        model = ConstDefault
        fields = ['config_name','default_value']
        labels = {
            'config_name': 'Constant Name',
            'default_value': 'Value'
        }
        widgets = {
            'config_name': forms.Select(
                attrs = {
                    'readonly': True,
                    'style': 'cursor: not-allowed; pointer-events: none; background-color: #d5dfed;'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super(ConstDefaultForm, self).__init__(*args, **kwargs)

    def clean_config_name(self):
        config_name = self.cleaned_data.get('config_name')
        return config_name


# Constant Default Event form 
# Inputs: Reviewers
class ConstDefaultEventForm(forms.ModelForm):
    class Meta:
        model = ConstDefaultEvent 
        fields = ['user_draft']
        labels = {
            'user_draft': 'Reviewers'
        }
        widgets = {
            'user_draft': forms.SelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super(ConstDefaultEventForm, self).__init__(*args, **kwargs)
        self.fields['user_draft'].queryset = User.objects.all().exclude(groups__name__in=['inventory only']).order_by('username')

    def clean_user_draft(self):
        user_draft = self.cleaned_data.get('user_draft')
        return user_draft

    def save(self, commit = True): 
        event = super(ConstDefaultEventForm, self).save(commit = False)
        if commit:
            event.save()
            if event.user_approver.exists():
                for user in event.user_approver.all():
                    event.user_draft.add(user)
                    event.user_approver.remove(user)
            event.save()
            return event


# Config Default Event form 
# Inputs: Reviewers
class ConfigDefaultEventForm(forms.ModelForm):
    class Meta:
        model = ConfigDefaultEvent 
        fields = ['user_draft']
        labels = {
            'user_draft': 'Reviewers'
        }
        widgets = {
            'user_draft': forms.SelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super(ConfigDefaultEventForm, self).__init__(*args, **kwargs)
        self.fields['user_draft'].queryset = User.objects.all().exclude(groups__name__in=['inventory only']).order_by('username')

    def clean_user_draft(self):
        user_draft = self.cleaned_data.get('user_draft')
        return user_draft

    def save(self, commit = True): 
        event = super(ConfigDefaultEventForm, self).save(commit = False)
        if commit:
            event.save()
            if event.user_approver.exists():
                for user in event.user_approver.all():
                    event.user_draft.add(user)
                    event.user_approver.remove(user)
            event.save()
            return event

# Config Default form
# Inputs: Config default values
class ConfigDefaultForm(forms.ModelForm):
    class Meta:
        model = ConfigDefault
        fields = ['config_name','default_value']
        labels = {
            'config_name': 'Constant Name',
            'default_value': 'Value'
        }
        widgets = {
            'config_name': forms.Select(
                attrs = {
                    'readonly': True,
                    'style': 'cursor: not-allowed; pointer-events: none; background-color: #d5dfed;'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super(ConfigDefaultForm, self).__init__(*args, **kwargs)

    def clean_config_name(self):
        config_name = self.cleaned_data.get('config_name')
        return config_name

# Configuration/Constant Copy Form
# Inputs: Part 
class ConfPartCopyForm(forms.Form):
    from_part = forms.ModelChoiceField(
        queryset = Part.objects.filter(part_type__name='Instrument'),
        required=False,
        label = 'Copy Configurations/Constants from Part'
    )

    def __init__(self, *args, **kwargs):
        self.part_id = kwargs.pop('part_id')
        super(ConfPartCopyForm, self).__init__(*args, **kwargs)
        self.fields['from_part'].queryset = Part.objects.filter(part_type__name='Instrument').exclude(id__in=str(self.part_id))

    def clean_from_part(self):
        from_part = self.cleaned_data.get('from_part')
        to_part = Part.objects.get(id=self.part_id)
        if from_part is not None:
            validate_from_part(to_part, from_part)
        return from_part

    def save(self):
        from_part = self.cleaned_data.get('from_part')
        if self.has_changed():
            copy_to_id = self.part_id
            copy_from_id = from_part.id
            copy_confignames(copy_to_id, copy_from_id)
        return from_part
        
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
    ConfigNameEvent, 
    ConfigName, 
    form=ConfigNameForm, 
    fields=(
        'name', 
        'config_type', 
        'include_with_calibrations'
    ), 
    extra=1, 
    can_delete=True
)

# Constant Default form instance generator for Parts
EventConstDefaultFormset = inlineformset_factory(
    ConstDefaultEvent, 
    ConstDefault, 
    form=ConstDefaultForm, 
    fields=('config_name', 'default_value'), 
    extra=0, 
    can_delete=True
)

# Constant Default form instance generator for Parts
EventConfigDefaultFormset = inlineformset_factory(
    ConfigDefaultEvent, 
    ConfigDefault, 
    form=ConfigDefaultForm, 
    fields=('config_name', 'default_value'), 
    extra=0, 
    can_delete=True
)


# Copy all Config/Constant Names across Parts
def copy_confignames(to_id, from_id):
    to_part = Part.objects.get(id=to_id)
    from_part = Part.objects.get(id=from_id)
    if from_part.config_name_events.exists():
        from_event = from_part.config_name_events.first()
        to_event = to_part.config_name_events.first()
        for name in from_event.config_names.all():
            ConfigName.objects.create(
                name = name.name,
                config_type = name.config_type,
                include_with_calibrations = name.include_with_calibrations,
                part = to_part,
                config_name_event = to_event
            )

# Validator for Part Config/Constant Copy
# When a Part is selected, from which to copy Config/Constant Names into another Part, the function checks if duplicate Names exist between the two Parts in question.
def validate_from_part(to_part, from_part):
    to_names = [name.name + name.config_type for name in to_part.config_names.all()]
    from_names = [name.name + name.config_type for name in from_part.config_names.all()]
    try:
        assert not any(from_name in to_names for from_name in from_names)
    except:
        raise ValidationError(
            _('Duplicate Config/Constant Names exist between Parts. Please select Part with unique Config/Constant Names.')
        )
    else: 
        pass