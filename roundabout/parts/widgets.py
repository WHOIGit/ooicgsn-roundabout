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

from django.forms.widgets import SelectMultiple

from django.template import loader
from django.utils.safestring import mark_safe

from .models import Part
from roundabout.locations.models import Location

class PartParentWidget(SelectMultiple):
    template_name = 'parts/part_parent_widget.html'

    def get_context(self, name, value, attrs):
        context = super(PartParentWidget, self).get_context(name, value, attrs)
        context.update({
            'parts_form_options': Part.objects.filter(parent=None).prefetch_related('children')
        })
        return context

    def render(self, name, value, attrs=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)


class PartLocationWidget(SelectMultiple):
    template_name = 'parts/part_location_widget.html'

    def get_context(self, name, value, attrs):
        context = super(PartLocationWidget, self).get_context(name, value, attrs)
        context.update({
            'locations_form_options': Location.objects.filter(tree_id=2).filter(level__gt=0)
        })
        return context

    def render(self, name, value, attrs=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)
