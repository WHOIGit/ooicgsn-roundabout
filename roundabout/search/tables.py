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

from django.utils.html import format_html
from django.urls import reverse
import django_tables2 as tables
from django.db.models import Count
from roundabout.inventory.models import Inventory
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision
from roundabout.userdefinedfields.models import FieldValue
from roundabout.admintools.models import Printer
from roundabout.assemblies.models import AssemblyPart,Assembly
from roundabout.builds.models import Build, BuildAction

class SearchTable(tables.Table):
    class Meta:
        template_name = "django_tables2/bootstrap4.html"

class InventoryTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Inventory
        fields = ("serial_number", 'part', 'location', "created_at","updated_at")

    def render_serial_number(self, value, record):
        item_url = reverse("inventory:inventory_detail", args=[record.pk])
        html_string = '<a href={}>{}</a>'.format(item_url, value)
        return format_html(html_string)
    def value_serial_number(self,record):
        return record.serial_number

    def render_part(self,record):
        item_url = reverse("parts:parts_detail", args=[record.part.pk])
        name = record.part.friendly_name_display()
        html_string = '{} <a href={}>➤</a>'.format(name, item_url)
        return format_html(html_string)
    def value_part(self,record):
        return record.part.name


class PartTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Part
        fields = ("part_number", 'name', 'part_type__name','inventory_count')

    part_type__name = tables.Column(verbose_name='Type')
    inventory_count = tables.Column(empty_values=())

    def render_part_number(self, value, record):
        item_url = reverse("parts:parts_detail", args=[record.pk])
        html_string = '<a href={}>{}</a>'.format(item_url, value)
        return format_html(html_string)

    def render_name(self,record):
        return record.friendly_name_display()

    def render_inventory_count(self,record):
        return record.get_part_inventory_count()
    def order_inventory_count(self, queryset, is_ascending):
        queryset = queryset.annotate(count=Count('inventory'))\
                           .order_by(("" if is_ascending else "-")+'count')
        return queryset, True


class BuildTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Build
        fields = ('build','name','build_number','location',"created_at","updated_at",'is_deployed','time_at_sea')

    build=tables.Column(empty_values=(),attrs={"th": {"style": "white-space:nowrap;"}})

    def render_build(self, record):
        item_url = reverse("builds:builds_detail", args=[record.pk])
        html_string = '<a href={}>{}-{}</a>'.format(item_url, record.assembly.assembly_number, record.build_number.replace('Build ',''))
        return format_html(html_string)


class AssemblyTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Assembly
        fields = ("assembly_number", 'name', 'assembly_type')

    def render_assembly_number(self, value, record):
        item_url = reverse("assemblies:assembly_detail", args=[record.pk])
        html_string = '<a href={}>{}</a>'.format(item_url, value)
        return format_html(html_string)

