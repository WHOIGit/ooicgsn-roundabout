from django import forms
from django.forms.models import inlineformset_factory
from django.utils import timezone
from bootstrap_datepicker_plus import DatePickerInput, DateTimePickerInput
from django.contrib.sites.models import Site

from .models import Build, BuildAction
from roundabout.inventory.models import Deployment, DeploymentAction


class BuildForm(forms.ModelForm):

    class Meta:
        model = Build
        fields = ['build_number', 'assembly', 'location', 'build_notes', ]
        labels = {
            'build_number': 'Build ID Number',
        }


class BuildActionLocationChangeForm(forms.ModelForm):

    class Meta:
        model = Build
        fields = ['location', 'detail']
        labels = {
            'detail': 'Add a Note',
        }

    def __init__(self, *args, **kwargs):
        super(BuildActionLocationChangeForm, self).__init__(*args, **kwargs)
        self.initial['detail'] = ''


class DeploymentForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location', 'deployment_number', 'build']

        labels = {
            'location': 'Current Location',
        }

        widgets = {
            'build': forms.HiddenInput(),
        }

    # Add custom date field to allow user to pick date for the Action
    date = forms.DateTimeField( widget=DateTimePickerInput(
            options={
                #"format": "MM/DD/YYYY, HH:mm", # moment date-time format
                "showClose": True,
                "showClear": True,
                "showTodayButton": True,
                "maxDate": timezone.now().strftime('%Y-%m-%d %H:%M'),
            }
        ),
        initial=timezone.now
    )

    def __init__(self, *args, **kwargs):
        super(DeploymentForm, self).__init__(*args, **kwargs)
        # Check what Site we're on, change form label if obs-rdb.whoi.edu
        current_site = Site.objects.get_current()
        if current_site.domain == 'obs-rdb.whoi.edu':
            deployment_number_label = 'Experiment Number'
        else:
            deployment_number_label = 'Deployment Number'

        self.fields['deployment_number'].label = deployment_number_label
