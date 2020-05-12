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
from decimal import Decimal

from django import forms
from django.forms.models import inlineformset_factory
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, Field
from django_summernote.widgets import SummernoteInplaceWidget, SummernoteWidget
from bootstrap_datepicker_plus import DatePickerInput, DateTimePickerInput
from django.contrib.sites.models import Site

from .models import Inventory, Deployment, Action, DeploymentSnapshot, PhotoNote
from .validators import validate_udffield_decimal
from roundabout.locations.models import Location
from roundabout.parts.models import Part, Revision
from roundabout.userdefinedfields.models import FieldValue
from roundabout.cruises.models import Cruise
# Import environment variables from .env files
import environ
env = environ.Env()


class InventoryForm(forms.ModelForm):
    serial_number = forms.CharField(strip=True,
        help_text='Serial Number auto-generated. Click here to override.',
        widget=forms.TextInput(attrs={'readonly':'readonly'}),
    )

    class Meta:
        model = Inventory
        fields = ['revision', 'serial_number', 'old_serial_number']
        labels = {
            'serial_number': 'Serial Number',
            'old_serial_number': 'Legacy Serial Number',
        }

    class Media:
        js = ('js/form-inventory.js',)

    def __init__(self, *args, **kwargs):

        super(InventoryForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            # Populate Revision field with only Revisions for this Part
            if self.instance.revision:
                revisions = Revision.objects.filter(part=self.instance.revision.part)
            else:
                revisions = Revision.objects.filter(part=self.instance.part)

            self.fields['revision'].queryset = revisions

            # Check if this Part has Custom fields, create fields if needed
            try:
                # Exclude any fields with Global Part Values
                custom_fields = self.instance.part.user_defined_fields.all()
            except Field.DoesNotExist:
                custom_fields = None

            if custom_fields:
                for field in custom_fields:
                    if field.field_type == 'IntegerField':
                        self.fields['udffield_' + str(field.id)] = forms.IntegerField(label=str(field.field_name), required=False,
                                                            help_text=str(field.field_description))
                    elif field.field_type == 'DecimalField':
                        self.fields['udffield_' + str(field.id)] = forms.CharField(label=str(field.field_name), required=False,
                                                            help_text=str(field.field_description), validators=[validate_udffield_decimal])
                    elif field.field_type == 'DateField':
                        self.fields['udffield_' + str(field.id)] = forms.DateTimeField(label=str(field.field_name), required=False,
                                                            help_text=str(field.field_description),
                                                            widget=DateTimePickerInput(
                                                                options={
                                                                    "format": "YYYY-MM-DD hh:mm:ss",
                                                                    "showClose": True,
                                                                    "showClear": True,
                                                                    "showTodayButton": True,
                                                                }
                                                            ))
                    elif field.field_type == 'BooleanField':
                        self.fields['udffield_' + str(field.id)] = forms.BooleanField(label=str(field.field_name), required=False,
                                                            help_text=str(field.field_description))
                    elif field.field_type == 'ChoiceField':
                        # Get the field options for this
                        options_dict = field.choice_field_options
                        options_list = [('', '- select one -')]

                        for option in options_dict['options']:
                            value = option['value']
                            label = value
                            if option['label']:
                                label = option['label']
                            form_option = (value, label)
                            options_list.append(form_option)

                        FIELD_CHOICES = (options_list)
                        self.fields['udffield_' + str(field.id)] = forms.ChoiceField(label=str(field.field_name), required=False,
                                                            help_text=str(field.field_description),
                                                            choices = FIELD_CHOICES)
                    else:
                        self.fields['udffield_' + str(field.id)] = forms.CharField(label=str(field.field_name), required=False,
                                                            help_text=str(field.field_description))

                    #Check if this inventory object has values for these fields, set initial values if true
                    try:
                        fieldvalue = self.instance.fieldvalues.filter(field_id=field.id).latest(field_name='created_at')
                    except FieldValue.DoesNotExist:
                        fieldvalue = None

                    if fieldvalue:
                        self.initial['udffield_' + str(field.id)] = fieldvalue.field_value


class InventoryAddForm(forms.ModelForm):
    RDB_SERIALNUMBER_CREATE = env.bool('RDB_SERIALNUMBER_CREATE', default=False)
    if RDB_SERIALNUMBER_CREATE:
        serial_number = forms.CharField(strip=True,
            help_text='Serial Number auto-generated. Click here to override.',
            widget=forms.TextInput(attrs={'readonly':'readonly'}),
        )
    else:
        serial_number = forms.CharField(strip=True)

    class Meta:
        model = Inventory
        fields = ['part', 'revision', 'serial_number', 'old_serial_number', 'location']
        labels = {
            'part': 'Select Part Template',
            'serial_number': 'Serial Number',
            'old_serial_number': 'Legacy Serial Number',
        }

    class Media:
        js = ('js/form-inventory-basic.js',)

    def __init__(self, *args, **kwargs):
        if 'parent_pk' in kwargs:
            self.parent = kwargs.pop('parent_pk')
        else:
            self.parent = None

        if 'current_location' in kwargs:
            self.current_location = kwargs.pop('current_location')
        else:
            self.current_location = None

        super(InventoryAddForm, self).__init__(*args, **kwargs)

        if self.parent:
            parent = Inventory.objects.get(id=self.parent)
            part_list = Part.objects.get(id=parent.part.id)
            self.fields['part'].queryset = part_list


class ActionLocationChangeForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['location', 'detail']
        labels = {
            'detail': 'Add a Note',
        }

    def __init__(self, *args, **kwargs):
        super(ActionLocationChangeForm, self).__init__(*args, **kwargs)
        #root_node = Location.objects.get(root_type='Land')
        #location_list = root_node.get_descendants()
        #self.fields['location'].queryset = location_list
        self.initial['detail'] = ''


class ActionSubassemblyChangeForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['location', 'parent', 'build', 'assembly_part', 'assigned_destination_root', 'detail']
        labels = {
            'detail': 'Add a Note',
        }
        widgets = {
            'parent': forms.HiddenInput(),
            'build': forms.HiddenInput(),
            'assembly_part': forms.HiddenInput(),
            'assigned_destination_root': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super(ActionSubassemblyChangeForm, self).__init__(*args, **kwargs)
        """
        part_parent = Part.objects.get(id=self.instance.part.id).get_ancestors(ascending=True, include_self=False).first()
        if part_parent:
            self.fields['parent'].queryset = Inventory.objects.filter(part_id=part_parent.id).filter(location_id=self.instance.location.id)
            """
        self.initial['detail'] = ''
        self.initial['parent'] = ''
        self.initial['build'] = ''
        self.initial['assembly_part'] = ''
        self.initial['assigned_destination_root'] = ''


class ActionRemoveFromBuildForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['location', 'detail', 'parent', 'build', 'assembly_part']
        widgets = {
            'parent': forms.HiddenInput(),
            'build': forms.HiddenInput(),
            'assembly_part': forms.HiddenInput(),
        }
        labels = {
            'location': 'Select new Location for item',
            'detail': 'Reasons for removing from Build',
        }

    def __init__(self, *args, **kwargs):
        super(ActionRemoveFromBuildForm, self).__init__(*args, **kwargs)
        self.initial['parent'] = ''
        self.initial['build'] = ''
        self.initial['assembly_part'] = ''
        self.initial['detail'] = ''


class ActionRemoveDestinationForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['detail', 'parent', 'build', 'assembly_part', 'assigned_destination_root']
        widgets = {
            'parent': forms.HiddenInput(),
            'build': forms.HiddenInput(),
            'assembly_part': forms.HiddenInput(),
            'assigned_destination_root': forms.HiddenInput(),
        }
        labels = {
            'detail': 'Reasons for removing destination',
        }

    def __init__(self, *args, **kwargs):
        super(ActionRemoveDestinationForm, self).__init__(*args, **kwargs)
        self.initial['parent'] = ''
        self.initial['build'] = ''
        self.initial['assembly_part'] = ''
        self.initial['assigned_destination_root'] = ''
        self.initial['detail'] = ''


class ActionTestForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['test_type', 'test_result', 'detail']
        labels = {
            'detail': 'Note on Test Results',
        }

    def __init__(self, *args, **kwargs):
        super(ActionTestForm, self).__init__(*args, **kwargs)
        self.initial['detail'] = ''


class ActionNoteForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['detail']
        labels = {
            'detail': 'Add a Note',
        }
        widgets = {
            'detail': SummernoteWidget(),
        }

    def __init__(self, *args, **kwargs):
        super(ActionNoteForm, self).__init__(*args, **kwargs)
        self.initial['detail'] = ''


class ActionPhotoNoteForm(forms.ModelForm):
    photo_ids = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Action
        fields = ['detail', 'inventory', 'location']
        labels = {
            'detail': 'Add a Note',
        }
        widgets = {
            'inventory': forms.HiddenInput(),
            'location': forms.HiddenInput(),
            'detail': SummernoteWidget(),
        }


class ActionPhotoUploadForm(forms.ModelForm):

    class Meta:
        model = PhotoNote
        fields = ['photo', 'inventory']
        labels = {
            'detail': 'Add a Note',
        }
        widgets = {
            'inventory': forms.HiddenInput(),
            'detail': SummernoteWidget(),
        }


class ActionDeployInventoryForm(forms.Form):
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
                                label='Date Deployed',
                                help_text='Set all date/times to UTC time zone.',
    )
    cruise = forms.ModelChoiceField(queryset=Cruise.objects.all(),
                                    label='Cruise Deployed On')


class ActionHistoryNoteForm(forms.ModelForm):

    class Meta:
        model = Action
        fields = ['created_at', 'detail', 'inventory']
        labels = {
            'created_at': 'Date',
            'detail': 'Add a Note',
        }
        widgets = {
            'inventory': forms.HiddenInput(),
            'created_at': forms.DateInput(),
            'detail': SummernoteWidget(),
        }


class ActionFlagForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['flag', 'detail']
        labels = {
            'flag': 'Flag Part',
            'detail': 'Details',
        }

    def __init__(self, *args, **kwargs):
        super(ActionFlagForm, self).__init__(*args, **kwargs)
        self.initial['detail'] = ''


class ActionMoveToTrashForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['location', 'detail', 'parent', 'deployment', 'assembly_part', 'assigned_destination_root', 'build']
        widgets = {
            'location': forms.HiddenInput(),
            'parent': forms.HiddenInput(),
            'deployment': forms.HiddenInput(),
            'assembly_part': forms.HiddenInput(),
            'assigned_destination_root': forms.HiddenInput(),
            'build': forms.HiddenInput(),
        }
        labels = {
            'detail': 'Reasons for moving to Trash Bin',
        }

    def __init__(self, *args, **kwargs):
        super(ActionMoveToTrashForm, self).__init__(*args, **kwargs)
        self.initial['location'] = Location.objects.get(root_type='Trash')
        self.initial['parent'] = ''
        self.initial['deployment'] = ''
        self.initial['assembly_part'] = ''
        self.initial['assigned_destination_root'] = ''
        self.initial['build'] = ''
        self.initial['detail'] = ''


class DeploymentForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location', 'deployment_number', 'final_location', 'build']

        labels = {
            'location': 'Current Location',
            'final_location': 'Deployment ID',
            'build': 'Select an Assembly Build',
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

        # Limit final_location choices to only Sea locations
        root_node = Location.objects.get(root_type='Sea')
        location_list = root_node.get_descendants()
        self.fields['final_location'].queryset = location_list


class DeploymentActionBurninForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location',]
        labels = {
            'location': 'Select Location for Burn In',
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
        widgets = {
            'location': forms.HiddenInput()
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
        self.initial['location'] = self.instance.final_location

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


class DeploymentSnapshotForm(forms.ModelForm):

    class Meta:
        model = DeploymentSnapshot
        fields = ['notes']
        labels = {
            'detail': 'Notes on Snapshot',
        }

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk')
        super(DeploymentSnapshotForm, self).__init__(*args, **kwargs)
        #self.fields['location'].queryset = Location.objects.exclude(id=self.pk)
