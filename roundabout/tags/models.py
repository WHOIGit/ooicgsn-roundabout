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

from roundabout.inventory.models import Inventory, AssemblyPart
from roundabout.parts.models import Part, Revision
from roundabout.configs_constants.models import ConfigValue, ConfigName

class Tag(models.Model):
    COLOR_CHOICES = [('primary', 'Blue'),
                     ('secondary', 'Grey'),
                     ('success', 'Green'),
                     ('danger', 'Red'),
                     ('warning', 'Orange'),
                     ('info', 'Light Blue'),
                     ('light', 'Light'),
                     ('dark', 'Dark'),
                     ]
    text = models.CharField(max_length=255)
    color = models.CharField(max_length=255, default='warning', choices=COLOR_CHOICES)
    pill = models.BooleanField(default=False)
    assembly_part = models.ForeignKey(AssemblyPart, related_name='tags', null=True, on_delete=models.CASCADE)
    config_name = models.ForeignKey(ConfigName, related_name='tags', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.text

    def get_object_type(self):
        return 'Tag'

    @property
    def tooltip(self):
        return self.text.format('{' + str(self.config_name) + '}')
