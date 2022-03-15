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
from django.utils import timezone
from bootstrap_datepicker_plus import DateTimePickerInput
from roundabout.ooi_ci_tools.models import CruiseEvent
from roundabout.calibrations.utils import reviewer_users

from .models import *
from roundabout.users.models import User


class VesselForm(forms.ModelForm):
    user_draft = forms.ModelMultipleChoiceField(
        queryset = User.objects.all().exclude(groups__name__in=['inventory only']).order_by('username'),
        required=False,
        label = 'Select Reviewers'
    )
    class Meta:
        model = Vessel
        fields = '__all__'
        labels = {
            'length': 'Length (m)',
            'max_speed': 'Max speed (m/s)',
            'max_draft': 'Max draft (m)',
        }
        number_err_message = 'Enter a value 0.1 - 999.9 in the format NNN.N, with or without leading zeros or a decimal place.'
        error_messages = {
            'length': {
                'max_digits': number_err_message,
                'min_value': number_err_message,
                'decimal_places': number_err_message,
            },
            'max_speed': {
                'max_digits': number_err_message,
                'min_value': number_err_message,
                'decimal_places': number_err_message,
            },
            'max_draft': {
                'max_digits': number_err_message,
                'min_value': number_err_message,
                'decimal_places': number_err_message,
            },
        }

VesselHyperlinkFormset = forms.models.inlineformset_factory(Vessel, VesselHyperlink, fields=('text', 'url'), extra=1, can_delete=True)


class CruiseForm(forms.ModelForm):
    user_draft = forms.ModelMultipleChoiceField(
        queryset = User.objects.all().exclude(groups__name__in=['inventory only']).order_by('username'),
        required=False,
        label = 'Select Reviewers'
    )
    # Add custom date fields
    cruise_start_date = forms.DateTimeField( widget=DateTimePickerInput(
            options={
                #"format": "MM/DD/YYYY, HH:mm", # moment date-time format
                "showClose": True,
                "showClear": True,
                "showTodayButton": False,
            }
        ),
        initial=timezone.now,
        help_text='Set all date/times to UTC time zone.',
    )

    cruise_stop_date = forms.DateTimeField( widget=DateTimePickerInput(
            options={
                #"format": "MM/DD/YYYY, HH:mm", # moment date-time format
                "showClose": True,
                "showClear": True,
                "showTodayButton": False,
            }
        ),
        #initial=timezone.now,
        help_text='Set all date/times to UTC time zone.',
    )

    class Meta:
        model = Cruise
        fields = '__all__'

CruiseHyperlinkFormset = forms.models.inlineformset_factory(Cruise, CruiseHyperlink, fields=('text', 'url'), extra=1, can_delete=True)





# Event form
# Inputs: Reviewers
class CruiseEventForm(forms.ModelForm):
    class Meta:
        model = CruiseEvent
        fields = ['user_draft']
        labels = {
            'user_draft': 'Reviewers'
        }
        widgets = {
            'user_draft': forms.SelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super(CruiseEventForm, self).__init__(*args, **kwargs)
        self.fields['user_draft'].queryset = reviewer_users()

    def clean_user_draft(self):
        user_draft = self.cleaned_data.get('user_draft')
        return user_draft

    def save(self, commit = True):
        event = super(CruiseEventForm, self).save(commit = False)
        if commit:
            event.save()
            if event.user_approver.exists():
                for user in event.user_approver.all():
                    event.user_draft.add(user)
                    event.user_approver.remove(user)
            event.save()
            return event


# Event form
# Inputs: Reviewers
class VesselEventForm(forms.ModelForm):
    class Meta:
        model = CruiseEvent
        fields = ['user_draft']
        labels = {
            'user_draft': 'Reviewers'
        }
        widgets = {
            'user_draft': forms.SelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super(VesselEventForm, self).__init__(*args, **kwargs)
        self.fields['user_draft'].queryset = reviewer_users()

    def clean_user_draft(self):
        user_draft = self.cleaned_data.get('user_draft')
        return user_draft

    def save(self, commit = True):
        event = super(VesselEventForm, self).save(commit = False)
        if commit:
            event.save()
            if event.user_approver.exists():
                for user in event.user_approver.all():
                    event.user_draft.add(user)
                    event.user_approver.remove(user)
            event.save()
            return event