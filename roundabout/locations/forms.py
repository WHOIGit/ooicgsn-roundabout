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
from django.forms.models import inlineformset_factory
from django.contrib.sites.models import Site

from .models import Location



class LocationForm(forms.ModelForm):

    class Meta:
        model = Location
        fields = ['name', 'parent', 'location_type', 'location_id' ]
        labels = {
        'location_id': 'Location ID'
    }

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)

        # Default Location Types
        LOC_TYPES = (
            ('', ''),
            ('Array', 'Array'),
            ('Mooring', 'Mooring'),
        )

        # Custom Location Types for OBS
        LOC_TYPES_OBS = (
            ('', ''),
            ('Instrument', 'Instrument'),
        )

        current_site = Site.objects.get_current()

        if current_site.domain == 'obs-rdb.whoi.edu':
            self.fields['location_type'].choices = LOC_TYPES_OBS
        else:
            self.fields['location_type'].choices = LOC_TYPES
