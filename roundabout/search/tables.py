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

import django_tables2 as tables
from roundabout.inventory.models import Inventory
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision
from roundabout.userdefinedfields.models import FieldValue
from roundabout.admintools.models import Printer
from roundabout.assemblies.models import AssemblyPart,Assembly
from roundabout.builds.models import Build, BuildAction


class InventoryTable(tables.Table):
    class Meta:
        model = Inventory
        template_name = "django_tables2/bootstrap4.html"
        fields = ("serial_number", 'part__name', 'location__name','location__location_type', "created_at","updated_at")

class PartTable(tables.Table):
    class Meta:
        model = Part
        template_name = "django_tables2/bootstrap4.html"
        fields = ("part_number", 'friendly_name', 'part_type__name',"created_at","updated_at")

class BuildTable(tables.Table):
    class Meta:
        model = Build
        template_name = "django_tables2/bootstrap4.html"
        fields = ("build_number", 'assembly__name','location__name', "created_at","updated_at",'time_at_sea')

class AssemblyTable(tables.Table):
    class Meta:
        model = Assembly
        template_name = "django_tables2/bootstrap4.html"
        fields = ("assembly_number", 'name', "created_at","updated_at")
