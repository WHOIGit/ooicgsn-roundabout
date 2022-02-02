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
from pprint import pprint

from django import forms
from django.shortcuts import get_object_or_404
from django.forms.models import inlineformset_factory
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_summernote.widgets import SummernoteWidget
from bootstrap_datepicker_plus import DatePickerInput, DateTimePickerInput

from roundabout.ooi_ci_tools.models import ReferenceDesignator, ReferenceDesignatorEvent
from roundabout.ooi_ci_tools.forms import validate_reference_designator
from roundabout.calibrations.utils import reviewer_users

from .models import (
    Assembly,
    AssemblyPart,
    AssemblyType,
    AssemblyRevision,
    AssemblyDocument,
)

# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels

labels = set_app_labels()


class AssemblyForm(forms.ModelForm):
    revision_code = forms.CharField(
        strip=True,
        initial="A",
        help_text='Enter a Revision Code for the initial version of this Assembly. Defaults to "A"',
    )
    assembly_revision_to_copy = forms.ModelChoiceField(
        queryset=AssemblyRevision.objects.all(),
    )
    copy_default_configs = forms.BooleanField(
        required=False,
        initial=True,
        label="Copy default config values from Revision",
    )

    class Meta:
        model = Assembly
        fields = [
            "name",
            "assembly_type",
            "assembly_number",
            "description",
            "revision_code",
            "assembly_revision_to_copy",
            "copy_default_configs",
        ]
        labels = {
            "name": "%s Name" % (labels["label_assemblies_app_singular"]),
            "assembly_type": "%s Type" % (labels["label_assemblies_app_singular"]),
            "assembly_number": "%s ID Number"
            % (labels["label_assemblies_app_singular"]),
        }
        widgets = {
            "description": SummernoteWidget(),
        }

    def __init__(self, *args, **kwargs):

        if "assembly_to_copy_pk" in kwargs:
            self.assembly_to_copy_pk = kwargs.pop("assembly_to_copy_pk")
        else:
            self.assembly_to_copy_pk = None

        super(AssemblyForm, self).__init__(*args, **kwargs)
        self.fields["assembly_type"].required = True

        if self.instance.pk:
            del self.fields["revision_code"]

        if self.assembly_to_copy_pk:
            revisions = AssemblyRevision.objects.filter(
                assembly_id=self.assembly_to_copy_pk
            )
            self.fields["assembly_revision_to_copy"].queryset = revisions
            self.fields["assembly_revision_to_copy"].initial = revisions.first()
        else:
            del self.fields["assembly_revision_to_copy"]
            del self.fields["copy_default_configs"]


class AssemblyRevisionForm(forms.ModelForm):
    copy_default_configs = forms.BooleanField(
        required=False,
        initial=True,
        label="Copy default config values from Revision",
    )
    assembly_revision_to_copy = forms.ModelChoiceField(
        queryset=AssemblyRevision.objects.all(),
    )

    class Meta:
        model = AssemblyRevision
        fields = [
            "copy_default_configs",
            "assembly_revision_to_copy",
            "revision_code",
            "created_at",
            "revision_note",
            "assembly",
        ]
        labels = {
            "created_at": "Release Date",
            "note": "Revision Notes",
        }
        widgets = {
            "created_at": DatePickerInput(
                options={
                    "format": "MM/DD/YYYY",  # moment date-time format
                    "showClose": True,
                    "showClear": True,
                    "showTodayButton": True,
                }
            ),
            "revision_note": SummernoteWidget(),
            "assembly": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        if "assembly_pk" in kwargs:
            self.assembly_pk = kwargs.pop("assembly_pk")
        else:
            self.assembly_pk = None

        if "assembly_revision_pk" in kwargs:
            self.assembly_revision_pk = kwargs.pop("assembly_revision_pk")
        else:
            self.assembly_revision_pk = None

        super(AssemblyRevisionForm, self).__init__(*args, **kwargs)
        # remove copy fields if this is an Update action
        if self.instance.pk:
            del self.fields["copy_default_configs"]
            del self.fields["assembly_revision_to_copy"]

        # if assembly_revision_pk exists, direct copy from a Revision.
        # set "assembly_revision_to_copy" field and hide it
        if self.assembly_revision_pk:
            assembly_revision_to_copy = AssemblyRevision.objects.get(
                id=self.assembly_revision_pk
            )
            self.fields["assembly_revision_to_copy"].initial = assembly_revision_to_copy
            self.fields["assembly_revision_to_copy"].widget = forms.HiddenInput()
        # Populate Revision field with only Revisions for this Part
        elif self.assembly_pk:
            revisions = AssemblyRevision.objects.filter(assembly_id=self.assembly_pk)
            self.fields["assembly_revision_to_copy"].queryset = revisions
            self.fields["assembly_revision_to_copy"].initial = revisions.first()

    def clean_revision_code(self):
        # Need to check if the Revision Code is already in use on this Assembly
        revision_code = self.cleaned_data["revision_code"]
        try:
            previous_revision = AssemblyRevision.objects.get(
                id=self.assembly_revision_pk
            )
            revisions = AssemblyRevision.objects.filter(
                assembly=previous_revision.assembly
            )

            for revision in revisions:
                if revision.revision_code == revision_code:
                    raise ValidationError(
                        "Revision Code already in use on this Assembly. Choose unique code."
                    )
        except:
            pass

        return revision_code


AssemblyRevisionFormset = inlineformset_factory(
    Assembly,
    AssemblyRevision,
    form=AssemblyRevisionForm,
    fields=("revision_code", "revision_note"),
    widgets={
        "revision_note": SummernoteWidget(),
    },
    extra=1,
    can_delete=False,
)
AssemblyDocumentationFormset = inlineformset_factory(
    AssemblyRevision,
    AssemblyDocument,
    fields=("name", "doc_type", "doc_link"),
    extra=1,
    can_delete=True,
)


class AssemblyPartForm(forms.ModelForm):
    # updated_refdes_name = forms.CharField(required=False)

    class Meta:
        model = AssemblyPart
        fields = ["assembly_revision", "part", "parent", "note"]
        labels = {
            "part": "Select Part Template",
            "parent": "Parent %s Part" % (labels["label_assemblies_app_singular"]),
            "note": "Design Notes",
        }

        widgets = {"assembly_revision": forms.HiddenInput()}

    class Media:
        js = ("js/form-assemblyparts.js",)

    def __init__(self, *args, **kwargs):

        if "assembly_revision_pk" in kwargs:
            self.assembly_revision_pk = kwargs.pop("assembly_revision_pk")
        else:
            self.assembly_revision_pk = None

        if "parent_pk" in kwargs:
            self.parent_pk = kwargs.pop("parent_pk")
        else:
            self.parent_pk = None

        super(AssemblyPartForm, self).__init__(*args, **kwargs)
        # self.fields['parent'].queryset = MooringPart.objects.none()
        # self.fields['parent'].queryset = AssemblyPart.objects.filter(id=self.parent_pk)
        if self.assembly_revision_pk:
            self.fields["parent"].queryset = AssemblyPart.objects.filter(
                assembly_revision_id=self.assembly_revision_pk
            )
        elif self.instance.pk:
            self.fields["parent"].queryset = AssemblyPart.objects.filter(
                assembly_revision=self.instance.assembly_revision
            )


class AssemblyTypeForm(forms.ModelForm):
    class Meta:
        model = AssemblyType
        fields = ["name"]
        labels = {
            "name": "%s Type Name" % (labels["label_assemblies_app_singular"]),
        }


"""
Custom Deletion form for AssemblyType
User needs to be able to choose a new AssemblyType for existing Assemblies or they
disappear from tree nav
"""


class AssemblyTypeDeleteForm(forms.Form):
    new_assembly_type = forms.ModelChoiceField(
        label="Select new Assembly Type", queryset=AssemblyType.objects.all()
    )

    def __init__(self, *args, **kwargs):
        assembly_type_pk = kwargs.pop("pk")
        assembly_type_to_delete = get_object_or_404(AssemblyType, id=assembly_type_pk)

        super(AssemblyTypeDeleteForm, self).__init__(*args, **kwargs)
        # Check if this PartType has IPart Templates, remove new field if false
        if not assembly_type_to_delete.assemblies.exists():
            self.fields["new_assembly_type"].required = False
            self.fields["new_assembly_type"].widget = forms.HiddenInput()

        # remove this object from the possible replacements
        self.fields["new_assembly_type"].queryset = AssemblyType.objects.exclude(
            id=assembly_type_to_delete.id
        )


# Config Default Event form
# Inputs: Reviewers
class ReferenceDesignatorEventForm(forms.ModelForm):
    class Meta:
        model = ReferenceDesignatorEvent
        fields = ["user_draft", "reference_designator"]
        labels = {
            "user_draft": "Reviewers",
            "reference_designator": "Reference Designator",
        }
        widgets = {"user_draft": forms.SelectMultiple()}

    def __init__(self, *args, **kwargs):
        super(ReferenceDesignatorEventForm, self).__init__(*args, **kwargs)
        self.fields["user_draft"].queryset = reviewer_users()
        self.fields["reference_designator"].required = False

    def clean_user_draft(self):
        user_draft = self.cleaned_data.get("user_draft")
        return user_draft

    def save(self, commit=True):
        event = super(ReferenceDesignatorEventForm, self).save(commit=False)
        if commit:
            event.save()
            if event.user_approver.exists():
                for user in event.user_approver.all():
                    event.user_draft.add(user)
                    event.user_approver.remove(user)
            event.save()
            assm_obj = AssemblyPart.objects.get(id=event.assembly_part.id)
            assm_obj.reference_designator = event.reference_designator
            assm_obj.save()
            return event


# Reference Designator form
# Inputs: Reference Designator values
class ReferenceDesignatorForm(forms.ModelForm):
    class Meta:
        model = ReferenceDesignator
        fields = [
            "refdes_name",
            "toc_l1",
            "toc_l2",
            "toc_l3",
            "instrument",
            "manufacturer",
            "model",
            "min_depth",
            "max_depth",
        ]
        labels = {
            "refdes_name": "Reference Designator Name",
            "toc_l1": "TOC_L1",
            "toc_l2": "TOC_L2",
            "toc_l3": "TOC_L3",
            "instrument": "Instrument",
            "manufacturer": "Manufacturer",
            "model": "Model",
            "min_depth": "Min Depth",
            "max_depth": "Max Depth",
        }
        widgets = {
            "refdes_name": forms.TextInput(attrs={"style": "width: 350px;"}),
            "toc_l1": forms.TextInput(attrs={"style": "width: 350px;"}),
            "toc_l2": forms.TextInput(attrs={"style": "width: 350px;"}),
            "toc_l3": forms.TextInput(attrs={"style": "width: 350px;"}),
            "instrument": forms.TextInput(attrs={"style": "width: 350px;"}),
            "manufacturer": forms.TextInput(attrs={"style": "width: 350px;"}),
            "model": forms.TextInput(attrs={"style": "width: 350px;"}),
            "min_depth": forms.TextInput(attrs={"style": "width: 350px;"}),
            "max_depth": forms.TextInput(attrs={"style": "width: 350px;"}),
        }

    def __init__(self, *args, **kwargs):
        super(ReferenceDesignatorForm, self).__init__(*args, **kwargs)

    def clean_refdes_name(self):
        name = self.cleaned_data.get("refdes_name")
        validate_reference_designator(name)
        return name


# Reference Designator form instance generator for Assembly parts
EventReferenceDesignatorFormset = ReferenceDesignatorForm

EventReferenceDesignatorAddFormset = ReferenceDesignatorForm
