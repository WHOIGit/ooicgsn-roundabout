from django import forms
from django.forms.models import inlineformset_factory
from django.utils import timezone
from bootstrap_datepicker_plus import DatePickerInput, DateTimePickerInput
from django.contrib.sites.models import Site
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, Field

from .models import Build, BuildAction
from roundabout.inventory.models import Deployment, DeploymentAction
from roundabout.locations.models import Location


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


class BuildActionFlagForm(forms.ModelForm):

    class Meta:
        model = Build
        fields = ['flag', 'detail']
        labels = {
            'flag': 'Flag Part',
            'detail': 'Details',
        }

    def __init__(self, *args, **kwargs):
        super(BuildActionFlagForm, self).__init__(*args, **kwargs)
        self.initial['detail'] = ''


class BuildActionTestForm(forms.ModelForm):

    class Meta:
        model = Build
        fields = ['detail']
        labels = {
            'detail': 'Note on Test Results',
        }

    def __init__(self, *args, **kwargs):
        super(BuildActionTestForm, self).__init__(*args, **kwargs)
        self.initial['detail'] = ''


class DeploymentForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location', 'deployment_number', 'build', 'deployed_location']

        labels = {
            'location': 'Current Location',
            'deployed_location': 'Final Deploy Location',
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


class DeploymentActionBurninForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location', 'deployed_location']
        labels = {
            'location': 'Select Location for Burn In',
            'deployed_location': 'Final Deploy Location',
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
        super(DeploymentActionBurninForm, self).__init__(*args, **kwargs)
        root_node = Location.objects.get(root_type='Land')
        location_list = root_node.get_descendants()
        self.fields['location'].queryset = location_list


class DeploymentActionDeployForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location',]
        labels = {
            'location': 'Deployment Location',
        }

    # Add custom date field to allow user to pick date for the Action record
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
    # Add lat/long, depth fields for the Action record
    latitude = forms.DecimalField()
    longitude = forms.DecimalField()
    depth = forms.IntegerField(label='Depth in Meters', min_value=0)

    def __init__(self, *args, **kwargs):
        super(DeploymentActionDeployForm, self).__init__(*args, **kwargs)
        self.initial['location'] = self.instance.deployed_location

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field('date'),
            ),
            Div(
                Field('latitude', wrapper_class='col-md-4'),
                Field('longitude', wrapper_class='col-md-4'),
                Field('depth', wrapper_class='col-md-4'),
                css_class='form-row'
            ),
            Div(
                Field('location'),
            )
        )


class DeploymentActionRecoverForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location',]
        labels = {
            'location': 'Select Land location to recover Deployment to:',
        }

    # Add custom date field to allow user to pick date for the Action
    date = forms.DateTimeField( widget=DateTimePickerInput(
            options={
                #"format": "MM/DD/YYYY, HH:mm:ss", # moment date-time format
                "showClose": True,
                "showClear": True,
                "showTodayButton": True,
                "maxDate": timezone.now().strftime('%Y-%m-%d %H:%M'),
            }
        ),
        initial=timezone.now()
    )

    def __init__(self, *args, **kwargs):
        super(DeploymentActionRecoverForm, self).__init__(*args, **kwargs)
        root_node = Location.objects.get(root_type='Land')
        location_list = root_node.get_descendants()
        self.fields['location'].queryset = location_list


class DeploymentActionRetireForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location',]
        widgets = {
            'location': forms.HiddenInput()
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
        super(DeploymentActionRetireForm, self).__init__(*args, **kwargs)
        self.initial['location'] = Location.objects.get(root_type='Retired')
