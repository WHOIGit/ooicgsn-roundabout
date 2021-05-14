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
from dateutil import parser

from roundabout.inventory.models import Inventory, Action, Deployment
from roundabout.locations.models import Location
from roundabout.parts.models import Part
from roundabout.userdefinedfields.models import Field, FieldValue
from roundabout.users.models import User

register = template.Library()

# Get the historical list of custom field values, return as queryset
@register.simple_tag
def get_udf_field_value_history(field, item):
    fieldvalues = FieldValue.objects.filter(field=field).filter(inventory=item).order_by('-created_at')

    for value in fieldvalues:
        #Check if UDF field is a DateField, if so format date for display
        if value.field.field_type == 'DateField':
            try:
                dt = parser.parse(value.field_value)
                value.field_value = dt.strftime("%m-%d-%Y %H:%M:%S")
            except:
                pass

    return fieldvalues


@register.simple_tag
def get_inventory_assembly_part_dictionary(inventory_qs):
    inventory_dict = {}
    for i in inventory_qs.all():
        inventory_dict[i.assembly_part_id] = i.id
    return inventory_dict


@register.simple_tag
def logged_user_is_reviewer(inv,logged_user):
    if inv.inventory_calibrationevents.exists():
        if logged_user.reviewer_calibrationevents.exists():
            found_events = inv.inventory_calibrationevents.filter(user_draft__in=[logged_user])
            if found_events:
                return True
    if inv.inventory_configevents.exists():
        if logged_user.reviewer_configevents.exists():
            found_events = inv.inventory_configevents.filter(user_draft__in=[logged_user])
            if found_events:
                return True
    return False


@register.simple_tag
def get_inventory_destination_dictionary(assigned_destination_root):
    inventory_dict = {}
    inventory_qs = Inventory.objects.filter(assigned_destination_root=assigned_destination_root)
    for i in inventory_qs.all():
        inventory_dict[i.assembly_part_id] = i.id
    return inventory_dict


@register.simple_tag
def get_inventory_queryset_by_deployment(dep_pk):
    queryset = Inventory.objects.filter(deployment_id=dep_pk)
    return queryset


@register.simple_tag
def get_inventory_list_by_location(location):
    if location.builds.exists():
        queryset = location.inventory.filter(build__isnull=True).filter(assembly_part__isnull=True).prefetch_related('part__part_type')
    else:
        queryset = location.inventory.filter(assembly_part__isnull=True).prefetch_related('part__part_type')
    return queryset


@register.simple_tag
def get_inventory_snapshot_list_by_location(location, dep):
    if location.deployment_snapshot.exists():
        queryset = location.inventory_snapshot.filter(deployment=dep).prefetch_related('inventory__part__part_type')
    else:
        queryset = location.inventory_snapshot.filter(deployment=dep).prefetch_related('inventory__part__part_type')
    return queryset


@register.simple_tag
def get_inventory_list_by_location_with_destination(location):
    queryset = location.inventory.filter(assembly_part__isnull=False).filter(build__isnull=True).filter(assigned_destination_root__isnull=False).prefetch_related('part__part_type')
    return queryset


@register.simple_tag
def get_part_by_inventory(part_pk):
    queryset = Part.objects.get(id=part_pk).get_family()
    return queryset

### FILTERS ###

# Get the Custom Field name from the Parts model
@register.filter
def get_custom_field_details_by_part(field_id, part):
    fields = part.custom_fields['fields']
    for field in fields:
        if field['field_id'] == field_id:
            field_name = field['field_name']
    return field_name

# Custom filter to get dictionary values by key
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

# Custom tag for diagnostics
@register.simple_tag
def debug_object_dump(var):
    return vars(var)
