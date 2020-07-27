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
from roundabout.calibrations.models import CalibrationEvent, CoefficientValueSet


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
        fields = []
        base_shown_cols = []
        attrs = {'style':'display: block; overflow-x: auto;'}

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
        udf_accessors = ['fieldvalues__field__field_name','fieldvalues__field_value']
        base_shown_cols = ['serial_number', 'part__name', 'location__name']

    def set_column_default_show(self,table_data):
        search_cols = [col for col in self.sequence if col.startswith('searchcol-')]
        extra_cols = [col for col in self.sequence if col.startswith('extracol-')]
        udf_cols = [col for col in self.sequence if col.startswith(UDF_Column.prefix) \
                                                 or col.startswith('searchcol-'+UDF_Column.prefix)]
        self.column_default_show = self.Meta.base_shown_cols + search_cols

class PartTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Part
        base_shown_cols = ["part_number", 'name', 'part_type__name']

    def set_column_default_show(self,table_data):
        search_cols = [col for col in self.sequence if col.startswith('searchcol-')]
        extra_cols = [col for col in self.sequence if col.startswith('extracol-')]
        udf_cols = [col for col in self.sequence if col.startswith(UDF_Column.prefix) \
                                                 or col.startswith('searchcol-'+UDF_Column.prefix)]
        self.column_default_show = self.Meta.base_shown_cols + search_cols

class BuildTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Build
        base_shown_cols = ['build','assembly__assembly_type__name','location__name','time_at_sea','is_deployed']

    build=Column(empty_values=(), order_by=('assembly__assembly_number','build_number'), attrs={'style':'white-space: nowrap;'})

    def render_build(self, record):
        item_url = reverse("builds:builds_detail", args=[record.pk])
        ass_num = record.assembly.assembly_number or record.assembly.name
        html_string = '<a href={}>{}-{}</a>'.format(item_url, ass_num, record.build_number.replace('Build ',''))
        return format_html(html_string)
    def value_build(self,record):
        return '{}-{}'.format(record.assembly.assembly_number, record.build_number.replace('Build ',''))

class AssemblyTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Assembly
        base_shown_cols = ['assembly_number', 'name', 'assembly_type__name']

class CalibrationTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = CoefficientValueSet
        base_shown_cols = ['calibration_event__inventory__part__name','coefficient_name__calibration_name','calibration_event__calibration_date']

class ActionTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Action
        fields = ['action_type','user__name','created_at','detail']
        base_shown_cols = fields

#TODO move most field Column specifications to col_args section of views page.
