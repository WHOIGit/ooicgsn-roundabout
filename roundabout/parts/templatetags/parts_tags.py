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

from django import template
from roundabout.parts.models import Part
from roundabout.locations.models import Location
from roundabout.userdefinedfields.models import FieldValue

register = template.Library()

# Get the historical list of custom field values, return as queryset
@register.simple_tag
def get_udf_field_value_history(field, part):
    fieldvalues = FieldValue.objects.filter(field=field).filter(part=part).order_by('-created_at')
    return fieldvalues

@register.filter
def is_in(var, obj):
    return var in obj

@register.simple_tag
def define(val=None):
    return val

@register.simple_tag
def get_parts_list_by_type(type_pk):
    queryset = Part.objects.filter(part_type=type_pk)
    return queryset

@register.simple_tag
def get_parts_list_by_location(location_pk):
    queryset = Part.objects.filter(location=location_pk).filter(parent=None).prefetch_related('children')
    return queryset

@register.simple_tag
def get_parts_children(pk, location_pk):
    part = Part.objects.get(pk=pk)
    valid_parts = Part.objects.filter(location=location_pk)
    location = Location.objects.get(pk=location_pk)

    def descendants_by_location_tree(part, valid_parts):
        """
        Returns a tree-like structure with progeny for specific Location
        """
        tree = {}
        for f in part.children.all():
            if f in valid_parts:
                tree[f] = descendants_by_location_tree(f, valid_parts)
        return tree

    return descendants_by_location_tree(part, valid_parts)

@register.simple_tag
def logged_user_is_reviewer(part,logged_user):
    if part.part_coefficientnameevents.exists():
        if logged_user.reviewer_coefficientnameevents.exists():
            found_events = part.part_coefficientnameevents.filter(user_draft__in=[logged_user])
            if found_events:
                return True
    if part.part_confignameevents.exists():
        if logged_user.reviewer_confignameevents.exists():
            found_events = part.part_confignameevents.filter(user_draft__in=[logged_user])
            if found_events:
                return True
    return False