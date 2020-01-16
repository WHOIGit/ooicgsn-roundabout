from django import forms
from django.forms.models import inlineformset_factory
from django.utils import timezone
from bootstrap_datepicker_plus import DatePickerInput, DateTimePickerInput
from django.contrib.sites.models import Site
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, Field
from django_summernote.widgets import SummernoteInplaceWidget, SummernoteWidget

from .models import Build, BuildAction, BuildSnapshot, PhotoNote
from roundabout.inventory.models import Deployment, DeploymentAction
from roundabout.locations.models import Location


class BuildForm(forms.ModelForm):
    build_number = forms.CharField(strip=True,
        help_text='Serial Number auto-generated. Click here to override.',
        widget=forms.TextInput(attrs={'readonly':'readonly'}),
        label='Build Number',
    )

    class Meta:
        model = Build
        fields = ['assembly', 'build_number', 'location', 'build_notes', ]
        labels = {
            'build_notes': 'Build Notes',
        }

    class Media:
        js = ('js/form-builds.js',)


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


class BuildActionPhotoNoteForm(forms.ModelForm):
    photo_ids = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = BuildAction
        fields = ['detail', 'build', 'location']
        labels = {
            'detail': 'Add a Note',
        }
        widgets = {
            'build': forms.HiddenInput(),
            'location': forms.HiddenInput(),
            'detail': SummernoteWidget(),
        }


class BuildActionPhotoUploadForm(forms.ModelForm):

    class Meta:
        model = PhotoNote
        fields = ['photo', 'build']
        labels = {
            'detail': 'Add a Note',
        }
        widgets = {
            'build': forms.HiddenInput(),
            'detail': SummernoteWidget(),
        }


class BuildActionRetireForm(forms.ModelForm):

    class Meta:
        model = Build
        fields = ['location', 'detail', ]
        widgets = {
            'location': forms.HiddenInput(),
        }
        labels = {
            'detail': 'Reasons for retiring this Build',
        }

    def __init__(self, *args, **kwargs):
        super(BuildActionRetireForm, self).__init__(*args, **kwargs)
        self.initial['location'] = Location.objects.get(root_type='Retired')
        self.initial['detail'] = ''


class BuildSnapshotForm(forms.ModelForm):

    class Meta:
        model = BuildSnapshot
        fields = ['notes']
        labels = {
            'detail': 'Notes on Snapshot',
        }

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk')
        super(BuildSnapshotForm, self).__init__(*args, **kwargs)
        #self.fields['location'].queryset = Location.objects.exclude(id=self.pk)


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
                "showTodayButton": False,
            }
        ),
        initial=timezone.now,
        help_text='Set all date/times to UTC time zone.',
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
                "showTodayButton": False,
            }
        ),
        initial=timezone.now,
        help_text='Set all date/times to UTC time zone.',
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
                "showTodayButton": False,
                #"maxDate": timezone.now().strftime('%m/%d/%Y %H:%M'),
            }
        ),
        initial=timezone.now,
        help_text='Set all date/times to UTC time zone.',
    )
    # Add lat/long, depth fields for the Action record
    latitude = forms.DecimalField(required=False)
    longitude = forms.DecimalField(required=False)
    depth = forms.IntegerField(label='Depth in Meters', min_value=0, required=False)

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


class DeploymentActionDetailsForm(forms.ModelForm):

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
                "showTodayButton": False,
            }
        ),
        initial=timezone.now,
        help_text='Set all date/times to UTC time zone.',
    )
    # Add lat/long, depth fields for the Action record
    latitude = forms.DecimalField(required=False)
    longitude = forms.DecimalField(required=False)
    depth = forms.IntegerField(label='Depth in Meters', min_value=0, required=False)

    def __init__(self, *args, **kwargs):
        super(DeploymentActionDetailsForm, self).__init__(*args, **kwargs)
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
            'location': 'Select location to recover Deployment to:',
        }

    # Add custom date field to allow user to pick date for the Action record
    date = forms.DateTimeField( widget=DateTimePickerInput(
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

    def __init__(self, *args, **kwargs):
        super(DeploymentActionRecoverForm, self).__init__(*args, **kwargs)
        root_node = Location.objects.get(root_type='Land')
        location_list = root_node.get_descendants()
        self.fields['location'].queryset = location_list
        self.fields['location'].required = True


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
                "showTodayButton": False,
            }
        ),
        initial=timezone.now,
        help_text='Set all date/times to UTC time zone.',
    )
