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
from django.contrib.auth.models import Group

register = template.Library()

# Template tag to assign a variable in a templates
@register.simple_tag
def define(val=None):
    return val


@register.filter
def get_model_name(value):
    return value.__class__.__name__


@register.filter(name='has_group')
def has_group(user, group_name):
    group =  Group.objects.get(name=group_name)
    try:
        return group in user.groups.all()
    except:
        return None


# Custom filter to get dictionary values by key
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


# filter Time at Sea duration field to show Hours/Minutes
@register.filter
def time_at_sea_display(duration):
    total_seconds = int(duration.total_seconds())
    days = total_seconds // (3600 * 24)
    hours = (total_seconds % (3600 * 24)) // 3600
    minutes = (total_seconds % 3600) // 60
    return '{} days {} hours {} min'.format(days, hours, minutes)
