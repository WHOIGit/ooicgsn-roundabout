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

from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey

# Create your models here.


class Location(MPTTModel):
    LOC_TYPES = (
        ('Array', 'Array'),
        ('Mooring', 'Mooring'),
        ('Instrument', 'Instrument'),
    )

    ROOT_TYPES = (
        ('Land', 'Land'),
        ('Sea', 'Sea'),
        ('Retired', 'Retired'),
        ('Snapshots', 'Snapshots'),
        ('Trash', 'Trash'),
    )

    name = models.CharField(max_length=100)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True, on_delete=models.SET_NULL)
    location_type = models.CharField(max_length=20, choices=LOC_TYPES, blank=True)
    location_id = models.CharField(max_length=100, blank=True)
    weight = models.IntegerField(default=0, blank=True, null=True)
    root_type = models.CharField(max_length=20, choices=ROOT_TYPES, blank=True)

    class MPTTMeta:
        order_insertion_by = ['weight', 'name']

    def __str__(self):
        return self.name

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return 'locations'

    def get_mooring_total_cost(self):
        tree = self.mooring_parts.all()
        total_cost = 0

        for item in tree:
            revision = item.part.revisions.first()
            cost = revision.unit_cost
            total_cost = total_cost + cost

        return total_cost
