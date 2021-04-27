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
from django.utils import timezone
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey


# Location app models


class Location(MPTTModel):
    ROOT_TYPES = (
        ("Land", "Land"),
        ("Sea", "Sea"),
        ("Retired", "Retired"),
        ("Snapshots", "Snapshots"),
        ("Trash", "Trash"),
    )

    name = models.CharField(max_length=100)
    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        db_index=True,
        on_delete=models.SET_NULL,
    )
    location_code = models.CharField(max_length=100, blank=True)
    weight = models.IntegerField(default=0, blank=True, null=True)
    root_type = models.CharField(max_length=20, choices=ROOT_TYPES, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ["weight", "name"]

    def __str__(self):
        return self.name

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return "locations"

    @property
    def root_location(self):
        return self.get_ancestors()[0].get_root_type_display()
