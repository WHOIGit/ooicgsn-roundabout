from django import forms
from django.forms.models import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit
from django_summernote.widgets import SummernoteInplaceWidget, SummernoteWidget

from .models import Inventory, Deployment, Action, DeploymentSnapshot, PhotoNote
from roundabout.locations.models import Location
from roundabout.parts.models import Part, Revision
from roundabout.moorings.models import MooringPart


class InventoryForm(forms.ModelForm):
    serial_number = forms.CharField(strip=True,
        help_text='Serial Number auto-generated. Click here to override.',
        widget=forms.TextInput(attrs={'readonly':'readonly'}),
    )

    class Meta:
        model = Inventory
        fields = ['revision', 'serial_number', 'old_serial_number', 'whoi_number', 'ooi_property_number']
        labels = {
            'serial_number': 'Serial Number',
            'old_serial_number': 'Legacy Serial Number',
            'whoi_number': 'WHOI Number',
            'ooi_property_number': 'OOI Property Number',
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

            # Remove Equipment specific fields unless item is Equipment
            if not self.instance.part.is_equipment:
                del self.fields['whoi_number']
                del self.fields['ooi_property_number']


class InventoryAddForm(forms.ModelForm):
    serial_number = forms.CharField(strip=True,
        help_text='Serial Number auto-generated. Click here to override.',
        widget=forms.TextInput(attrs={'readonly':'readonly'}),
    )

    class Meta:
        model = Inventory
        fields = ['part', 'revision', 'serial_number', 'old_serial_number', 'whoi_number', 'ooi_property_number', 'location']
        labels = {
            'part': 'Select Part Template',
            'serial_number': 'Serial Number',
            'old_serial_number': 'Legacy Serial Number',
            'whoi_number': 'WHOI Number',
            'ooi_property_number': 'OOI Property Number',
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

        # Remove Equipment specific fields unless item is Equipment
        if self.instance.pk:
            if not self.instance.part.is_equipment:
                del self.fields['whoi_number']
                del self.fields['ooi_property_number']


class ActionInventoryChangeForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['location', 'deployment', 'mooring_part', 'parent', 'detail']
        labels = {
            'detail': 'Add a Note',
        }

    class Media:
        js = ('js/form-inventory.js',)

    def __init__(self, *args, **kwargs):
        super(ActionInventoryChangeForm, self).__init__(*args, **kwargs)
        self.initial['detail'] = ''
        self.fields['parent'].queryset = Inventory.objects.none()
        self.fields['deployment'].queryset = Deployment.objects.none()
        self.fields['mooring_part'].queryset = MooringPart.objects.none()

        # Allow AJAX submissions by populating querysets for Django form check
        if 'part' in self.data:
            try:
                part_id = int(self.data.get('part'))
                mooring_parts = MooringPart.objects.filter(part_id=part_id)
                if mooring_parts:
                    mooring_parts_list = []
                    for mp in mooring_parts:
                        mooring_parts_list.append(mp.parent.part.id)
                    self.fields['parent'].queryset = Inventory.objects.filter(part_id__in=mooring_parts_list)

            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
        elif self.instance.pk:
            if self.instance.deployment:
                mooring_parts = MooringPart.objects.filter(part_id=self.instance.part.id).filter(location=self.instance.deployment.final_location)
            else:
                mooring_parts = MooringPart.objects.filter(part_id=self.instance.part.id)
                mooring_parts_list = []
                for mp in mooring_parts:
                    if mp.parent:
                        mooring_parts_list.append(mp.parent.part.id)
                        self.fields['parent'].queryset = Inventory.objects.filter(part_id__in=mooring_parts_list).filter(location=self.instance.location)
                    else:
                        self.fields['parent'].queryset = Inventory.objects.none()

        if 'location' in self.data:
            try:
                location_id = int(self.data.get('location'))
                self.fields['deployment'].queryset = Deployment.objects.filter(location_id=location_id)
                self.fields['parent'].queryset = Inventory.objects.filter(location_id=location_id)
                self.fields['mooring_part'].queryset = MooringPart.objects.all()
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
        elif self.instance.pk:
            self.fields['deployment'].queryset = Deployment.objects.filter(location_id=self.instance.location.id)

        if 'deployment' in self.data:
            try:
                deployment_id = int(self.data.get('deployment'))
                deployment = Deployment.objects.get(id=deployment_id)
                self.fields['mooring_part'].queryset = MooringPart.objects.filter(location=deployment.final_location)
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
        elif self.instance.pk:
            if self.instance.deployment:
                self.fields['mooring_part'].queryset = MooringPart.objects.filter(location=self.instance.deployment.final_location)
            elif self.instance.mooring_part:
                self.fields['mooring_part'].queryset = MooringPart.objects.filter(location=self.instance.mooring_part.location)
            else:
                self.fields['mooring_part'].queryset = MooringPart.objects.none()


class ActionLocationChangeForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['location', 'detail']
        labels = {
            'detail': 'Add a Note',
        }

    def __init__(self, *args, **kwargs):
        super(ActionLocationChangeForm, self).__init__(*args, **kwargs)
        root_node = Location.objects.get(name='Land')
        location_list = root_node.get_descendants()
        self.fields['location'].queryset = location_list
        self.initial['detail'] = ''


class ActionSubassemblyChangeForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['location', 'parent', 'deployment', 'mooring_part', 'assigned_destination_root', 'detail']
        labels = {
            'detail': 'Add a Note',
        }
        widgets = {
            'parent': forms.HiddenInput(),
            'deployment': forms.HiddenInput(),
            'mooring_part': forms.HiddenInput(),
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
        self.initial['deployment'] = ''
        self.initial['mooring_part'] = ''
        self.initial['assigned_destination_root'] = ''


class ActionRemoveFromDeploymentForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['location', 'detail', 'parent', 'deployment', 'mooring_part']
        widgets = {
            'parent': forms.HiddenInput(),
            'deployment': forms.HiddenInput(),
            'mooring_part': forms.HiddenInput(),
        }
        labels = {
            'location': 'Select new Location for item',
            'detail': 'Reasons for removing from Deployment',
        }

    def __init__(self, *args, **kwargs):
        super(ActionRemoveFromDeploymentForm, self).__init__(*args, **kwargs)
        self.initial['parent'] = ''
        self.initial['deployment'] = ''
        self.initial['mooring_part'] = ''
        self.initial['detail'] = ''


class ActionRemoveDestinationForm(forms.ModelForm):

    class Meta:
        model = Inventory
        fields = ['detail', 'parent', 'deployment', 'mooring_part', 'assigned_destination_root']
        widgets = {
            'parent': forms.HiddenInput(),
            'deployment': forms.HiddenInput(),
            'mooring_part': forms.HiddenInput(),
            'assigned_destination_root': forms.HiddenInput(),
        }
        labels = {
            'detail': 'Reasons for removing destination',
        }

    def __init__(self, *args, **kwargs):
        super(ActionRemoveDestinationForm, self).__init__(*args, **kwargs)
        self.initial['parent'] = ''
        self.initial['deployment'] = ''
        self.initial['mooring_part'] = ''
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
        fields = ['location', 'detail', 'parent', 'deployment', 'mooring_part', 'assigned_destination_root']
        widgets = {
            'location': forms.HiddenInput(),
            'parent': forms.HiddenInput(),
            'deployment': forms.HiddenInput(),
            'mooring_part': forms.HiddenInput(),
            'assigned_destination_root': forms.HiddenInput(),
        }
        labels = {
            'detail': 'Reasons for moving to Trash Bin',
        }

    def __init__(self, *args, **kwargs):
        super(ActionMoveToTrashForm, self).__init__(*args, **kwargs)
        self.initial['location'] = Location.objects.get(name='Trash Bin')
        self.initial['parent'] = ''
        self.initial['deployment'] = ''
        self.initial['mooring_part'] = ''
        self.initial['assigned_destination_root'] = ''
        self.initial['detail'] = ''


class DeploymentForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location', 'deployment_number', 'final_location']
        labels = {
            'location': 'Current Location',
            'final_location': 'Deployment ID',
        }

    def __init__(self, *args, **kwargs):
        super(DeploymentForm, self).__init__(*args, **kwargs)
        root_node = Location.objects.get(name='Sea')
        location_list = root_node.get_descendants()
        self.fields['final_location'].queryset = location_list


class DeploymentActionBurninForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location',]
        labels = {
            'location': 'Select Location for Burn In',
        }

    def __init__(self, *args, **kwargs):
        super(DeploymentActionBurninForm, self).__init__(*args, **kwargs)
        root_node = Location.objects.get(name='Land')
        location_list = root_node.get_descendants()
        self.fields['location'].queryset = location_list


class DeploymentActionDeployForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location',]
        widgets = {
            'location': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(DeploymentActionDeployForm, self).__init__(*args, **kwargs)
        self.initial['location'] = self.instance.final_location


class DeploymentActionRecoverForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location',]
        labels = {
            'location': 'Select Land location to recover Deployment to:',
        }

    def __init__(self, *args, **kwargs):
        super(DeploymentActionRecoverForm, self).__init__(*args, **kwargs)
        root_node = Location.objects.get(name='Land')
        location_list = root_node.get_descendants()
        self.fields['location'].queryset = location_list


class DeploymentActionRetireForm(forms.ModelForm):

    class Meta:
        model = Deployment
        fields = ['location',]
        widgets = {
            'location': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(DeploymentActionRetireForm, self).__init__(*args, **kwargs)
        self.initial['location'] = Location.objects.get(name='Retired')


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
