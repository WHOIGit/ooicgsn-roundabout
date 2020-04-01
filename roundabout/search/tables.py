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
from django.db.models import Count

import django_tables2 as tables
from django_tables2_column_shifter.tables import ColumnShiftTable

from roundabout.inventory.models import Inventory
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision
from roundabout.userdefinedfields.models import FieldValue
from roundabout.admintools.models import Printer
from roundabout.assemblies.models import AssemblyPart,Assembly
from roundabout.builds.models import Build, BuildAction
from roundabout.userdefinedfields.models import Field


UDF_FIELDS = list(Field.objects.all().order_by('id'))
class UDF_Column(tables.ManyToManyColumn):

    prefix = 'udf-'

    def __init__(self,udf,*args,**kwargs):
        self.udf = udf
        super().__init__(accessor='fieldvalues', verbose_name=udf.field_name, orderable=True, default='',
                         filter=lambda qs: qs.filter(field__id=udf.id, is_current=True))

    # TESTING
    #def foot_func(self, table, bound_column):
    #    a = [self.filter(getattr(x,self.accessor,None)) for x in table.data]
    #    print('FOOT',self.udf.id, a)
    #    s = len([x for x in a if x])
    #    return s

    #TESTING
    #def render(self, value):
    #    print('UDF_RENDER:', self.udf.field_name, self.filter(value) if value.exists() else self.default)
    #    return super().render(value)

class SearchTable(ColumnShiftTable):
    class Meta:
        template_name = "django_tables2/bootstrap4.html"

class InventoryTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Inventory
        fields = ['serial_number', 'part', 'part__part_number', 'location','revision__note', 'created_at', 'updated_at' ]

    serial_number = tables.Column(verbose_name='Serial Number')
    part__part_number = tables.Column(verbose_name='Part Number', visible = False)
    revision__note = tables.Column(verbose_name='Notes')

    def set_column_default_show(self,table_data):
        self.column_default_show = ['serial_number', 'part', 'part__part_number', 'location']

        try: actual_udf_IDs = set(table_data.values_list('fieldvalues__field__id',flat=True))
        except AttributeError: # sometimes qs is returned as a list
            qs_list = Field.objects.none()
            for x in table_data:
                qs_list = qs_list.union(x.part.user_defined_fields.all())
            actual_udf_IDs = list(qs_list.values_list('id',flat=True))

        for bound_col in self.columns:
            if bound_col.name.startswith(UDF_Column.prefix):
                udf_col = bound_col.column
                if udf_col.udf.id in actual_udf_IDs:
                    self.column_default_show.append(bound_col.name)
                    #bound_col.column.visible = False  # completely removes it from the interface, but will exist in export, but also does not allow for it to be shown again.
                    #bound_col.column.exclude_from_export = True # removes column from the export list!

    #TODO with filterview auto select filtere'd columns: https://stackoverflow.com/questions/52686382/dynamic-columns-with-singletablemixin-and-filterview-in-django

    def render_serial_number(self, value, record):
        item_url = reverse("inventory:inventory_detail", args=[record.pk])
        html_string = '<a href={}>{}</a>'.format(item_url, value)
        return format_html(html_string)
    def value_serial_number(self,record):
        #print(record.id)
        return record.serial_number

    def render_part(self,record):
        item_url = reverse("parts:parts_detail", args=[record.part.pk])
        name = record.part.friendly_name_display()
        html_string = '{} <a href={}>➤</a>'.format(name, item_url)
        return format_html(html_string)
    def value_part(self,record):
        return record.part.name

    def render_revision__note(self,value):
        return format_html(value)


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

