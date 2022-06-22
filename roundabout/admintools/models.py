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
from django.db.models import JSONField
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey

from roundabout.assemblies.models import AssemblyType
from roundabout.parts.models import Part
from roundabout.users.models import User
from roundabout.cruises.models import Cruise

# AdminTool models
class Printer(models.Model):
    PRINTER_TYPES = (
        ('Brady', 'Brady'),
        ('Zebra', 'Zebra'),
    )
    name = models.CharField(max_length=255, unique=False, db_index=True)
    ip_domain = models.CharField(max_length=255, unique=True)
    printer_type = models.CharField(max_length=20, choices=PRINTER_TYPES, default='Brady')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TempImport(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    column_headers = models.JSONField()
    update_existing_inventory = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class TempImportItem(models.Model):
    data = models.JSONField()
    tempimport = models.ForeignKey(TempImport, related_name='tempimportitems',
                                   on_delete=models.CASCADE, null=True, blank=False)

    def __str__(self):
        return str(self.id)


# Assembly base model
class TempImportAssembly(models.Model):
    name = models.CharField(max_length=255, unique=False)
    assembly_type = models.ForeignKey(AssemblyType, related_name='temp_assemblies',
                                    on_delete=models.SET_NULL, null=True, blank=True)
    assembly_number = models.CharField(max_length=100, unique=False, null=False, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# Assembly parts model
class TempImportAssemblyPart(MPTTModel):
    assembly = models.ForeignKey(TempImportAssembly, related_name='temp_assembly_parts',
                          on_delete=models.CASCADE, null=False, blank=False)
    part = models.ForeignKey(Part, related_name='temp_assembly_parts',
                          on_delete=models.CASCADE, null=False, blank=False)
    parent = TreeForeignKey('self', related_name='children',
                            on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    previous_id = models.IntegerField(null=True, blank=True)
    previous_parent = models.IntegerField(null=True, blank=True)
    note = models.TextField(blank=True)
    order =  models.CharField(max_length=255, null=True, blank=True)

    class MPTTMeta:
        order_insertion_by = ['order']

    def __str__(self):
        return self.part.name
