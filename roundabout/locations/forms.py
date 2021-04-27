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
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory
from django.contrib.sites.models import Site
from mptt.forms import TreeNodeChoiceField

from .models import Location


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["name", "parent", "location_code"]

    def clean_parent(self):
        if self.instance:
            print(self.instance)
            parent = self.cleaned_data["parent"]
            print(parent)

        if self.instance == parent:
            raise ValidationError("Location Parent cannot be self")
        return parent


"""
Custom Deletion form for Locations
User needs to be able to choose a new Location for Inventory/Builds
"""


class LocationDeleteForm(forms.Form):
    new_location = TreeNodeChoiceField(
        label="Select new Location", queryset=Location.objects.all()
    )

    def __init__(self, *args, **kwargs):
        location_pk = kwargs.pop("pk")
        location_to_delete = Location.objects.get(id=location_pk)

        super(LocationDeleteForm, self).__init__(*args, **kwargs)
        # Check if this Location has Inventory or Builds, remove new Location field if false
        if (
            not location_to_delete.inventory.exists()
            and not location_to_delete.builds.exists()
        ):
            self.fields["new_location"].required = False
            self.fields["new_location"].widget = forms.HiddenInput()
