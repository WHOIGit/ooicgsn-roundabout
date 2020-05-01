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

from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.db.models import Count

import django_tables2 as tables
from django_tables2.columns import Column, DateTimeColumn, BooleanColumn, ManyToManyColumn
from django_tables2_column_shifter.tables import ColumnShiftTable

from roundabout.parts.models import Part
from roundabout.builds.models import Build, BuildAction
from roundabout.inventory.models import Inventory, Action, DeploymentAction
from roundabout.assemblies.models import Assembly
from roundabout.userdefinedfields.models import Field


class UDF_Column(ManyToManyColumn):
    prefix = 'udf-'
    def __init__(self, udf, accessor, accessor_type=['Field','FieldValue'][0], footer_count=False, **kwargs):
        self.udf = udf
        self.accessor = accessor
        self.accessor_type = accessor_type
        if accessor_type == 'Field':
            col_name = '{} (Default)'.format(udf.field_name)
            udf_filter = self.field_filter
        else: # FieldValue
            col_name = udf.field_name
            udf_filter = self.fieldvalues_filter

        if footer_count:
            footer = self.footer_filter
        else:
            footer=None

        super().__init__(accessor=accessor, verbose_name=col_name, orderable=True, default='',
                         filter=udf_filter, footer=footer, **kwargs)

    def field_filter(self,qs):
        qs = qs.filter(id=self.udf.id)
        if qs: return qs[0].field_default_value
        return qs

    def fieldvalues_filter(self, qs):
        return qs.filter(field__id=self.udf.id, is_current=True)

    def footer_filter(self,table):
        # quite expensive to run. Activated with GET flag "show-udf-footer-count"
        field = 'id' if self.accessor_type=='Field' else 'field__id'  # for 'FieldValue'
        udf_vals = [getattr(row, self.accessor).filter(**{field:self.udf.id}) for row in table.data]
        return len([val for val in udf_vals if val])


class SearchTable(ColumnShiftTable):
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        base_shown_cols = []
        attrs = {'style':'display: block; overflow-x: auto;'}
        #attrs = {'style':'display: block; overflow-x: auto; white-space: nowrap;'}

    def set_column_default_show(self, table_data):
        if not self.Meta.base_shown_cols:
            self.column_default_show = None
        else:
            search_cols = [col for col in self.sequence if col.startswith('searchcol-')]
            extra_cols = [col for col in self.sequence if col.startswith('extracol-')]
            self.column_default_show = self.Meta.base_shown_cols + search_cols


class InventoryTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Inventory
        action_accessors = ['actions__latest__action_type', 'actions__latest__user__name', 'actions__latest__created_at', 'actions__latest__location__name', 'actions__latest__detail']
        udf_accessors = ['fieldvalues__field__field_name','fieldvalues__field_value']
        fields = ['serial_number','part__name','location__name','revision__note']
        base_shown_cols = ['serial_number', 'part__name', 'location__name']

    # default columns
    serial_number = Column(verbose_name='Serial Number', attrs={'style':'white-space: nowrap;'},
              linkify=dict(viewname="inventory:inventory_detail", args=[tables.A('pk')]))
    part__name = Column(verbose_name='Name')
    location__name = Column(verbose_name='Location')
    revision__note = Column(verbose_name='Notes')

    def set_column_default_show(self,table_data):
        search_cols = [col for col in self.sequence if col.startswith('searchcol-')]
        extra_cols = [col for col in self.sequence if col.startswith('extracol-')]
        udf_cols = [col for col in self.sequence if col.startswith(UDF_Column.prefix) \
                                                 or col.startswith('searchcol-'+UDF_Column.prefix)]
        self.column_default_show = self.Meta.base_shown_cols + search_cols

    def render_part(self,record):
        item_url = reverse("parts:parts_detail", args=[record.part.pk])
        name = record.part.name
        html_string = '{} <a href={}>➤</a>'
        return format_html(html_string,name, item_url)
    def value_part(self,record):
        return record.part.name

    def render_revision__note(self,value):
        return mark_safe(value)
    def value_revision__note(self,record):
        return record.revision.note

    def render_actions__latest__action_type(self,value):
        try: disp_value = [text for val,text in Action.ACT_TYPES if val==value][0]
        except IndexError: disp_value = value
        return disp_value

    def render_actions__latest__detail(self,value):
        return mark_safe(value)

class PartTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Part
        fields = ["part_number", 'name', 'part_type__name']
        base_shown_cols = fields

    part_number = Column(verbose_name='Part Number', attrs={'style':'white-space: nowrap;'},
                   linkify=dict(viewname='parts:parts_detail',args=[tables.A('pk')]))
    part_type__name = Column(verbose_name='Type')

    def render_name(self,record):
        return record.friendly_name_display()

    def set_column_default_show(self,table_data):
        search_cols = [col for col in self.sequence if col.startswith('searchcol-')]
        extra_cols = [col for col in self.sequence if col.startswith('extracol-')]
        udf_cols = [col for col in self.sequence if col.startswith(UDF_Column.prefix) \
                                                 or col.startswith('searchcol-'+UDF_Column.prefix)]
        self.column_default_show = self.Meta.base_shown_cols + search_cols

class BuildTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Build
        action_accessors = ['build_actions__latest__action_type', 'build_actions__latest__user__name', 'build_actions__latest__created_at','build_actions__latest__location__name','build_actions__latest__detail']
        fields = ['build','assembly__name','build_number','assembly__assembly_type__name','location__name','time_at_sea','is_deployed']
        base_shown_cols = ['build','assembly__assembly_type__name','location__name','time_at_sea','is_deployed']

    build=Column(empty_values=(), order_by=('assembly__assembly_number','build_number'), attrs={'style':'white-space: nowrap;'})
    location__name = Column(verbose_name='Location', accessor='location__name')
    assembly__assembly_type__name = Column(verbose_name='Type')

    def render_build(self, record):
        item_url = reverse("builds:builds_detail", args=[record.pk])
        ass_num = record.assembly.assembly_number or record.assembly.name
        html_string = '<a href={}>{}-{}</a>'.format(item_url, ass_num, record.build_number.replace('Build ',''))
        return format_html(html_string)
    def value_build(self,record):
        return '{}-{}'.format(record.assembly.assembly_number, record.build_number.replace('Build ',''))

    def render_build_actions__latest__action_type(self,value,record):
        try: disp_value = [text for val,text in BuildAction.ACT_TYPES if val==value][0]
        except IndexError: disp_value = value
        return disp_value

    def render_build_actions__latest__detail(self,value):
        return mark_safe(value)

class AssemblyTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Assembly
        fields = ['assembly_number', 'name', 'assembly_type__name', 'description']
        base_shown_cols = ['assembly_number', 'name', 'assembly_type__name']

    assembly_number = Column(verbose_name='Assembly Number', attrs={'style':'white-space: nowrap;'},
        linkify=dict(viewname='assemblies:assembly_detail',args=[tables.A('pk')]))
    assembly_type__name = Column(verbose_name='Type')
