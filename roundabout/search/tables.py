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
from django.urls import reverse
from django.utils.html import format_html
from django_tables2.columns import Column, DateColumn, DateTimeColumn, ManyToManyColumn
from django_tables2_column_shifter.tables import ColumnShiftTable

from roundabout.assemblies.models import Assembly
from roundabout.builds.models import Build
from roundabout.calibrations.models import CalibrationEvent
from roundabout.configs_constants.models import ConfigEvent
from roundabout.inventory.models import Inventory, Action
from roundabout.parts.models import Part


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
        if qs:
            return [qs[0].field_default_value]
        else:
            return ['―']

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


class ActionTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Action
        fields = ['action_type','user__name','created_at','detail']
        base_shown_cols = fields


class CalibrationTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = CalibrationEvent
        fields = ['inventory__serial_number','inventory__part__name','calibration_date','deployment','approved','user_approver__all__name','user_draft__all__name','created_at']
        base_shown_cols = ['inventory__serial_number','calibration_date','approved']

    inventory__serial_number = Column(verbose_name='Inventory SN', attrs={'style':'white-space: nowrap;'},
            linkify=dict(viewname="inventory:inventory_detail", args=[tables.A('inventory__pk')]))
    inventory__part__name = Column(verbose_name='Part',
            linkify=dict(viewname="parts:parts_detail", args=[tables.A('inventory__part__pk')]))
    calibration_date = DateColumn(verbose_name='Calibration Date', format='Y-m-d',
            linkify=dict(viewname="exports:calibration", args=[tables.A('pk')]))

    user_approver__all__name = ManyToManyColumn(verbose_name='Approvers', accessor='user_approver', transform=lambda x: x.name, default='')
    user_draft__all__name = ManyToManyColumn(verbose_name='Reviewers', accessor='user_draft', transform=lambda x: x.name, default='')

    coefficient_value_set__names = ManyToManyColumn(verbose_name='Coefficient Names',
            accessor='coefficient_value_sets', transform=lambda x: x.coefficient_name)
    coefficient_value_set__notes = ManyToManyColumn(verbose_name='Coefficient Notes',
            accessor='coefficient_value_sets', transform=lambda x: format_html('<b>{}:</b> [{}]<br>'.format(x.coefficient_name,x.notes)) if x.notes else '', separator='\n')

    detail = Column(verbose_name='CalibrationEvent Note', accessor='detail')
    created_at = DateTimeColumn(verbose_name='Date Entered', accessor='created_at', format='Y-m-d H:i')


class ConfigConstTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = ConfigEvent
        fields = ['inventory__serial_number','inventory__part__name','config_type','configuration_date','deployment','approved','user_approver__all__name','user_draft__all__name','created_at']
        base_shown_cols = ['inventory__serial_number','configuration_date','config_type','approved']

    inventory__serial_number = Column(verbose_name='Inventory SN', attrs={'style':'white-space: nowrap;'},
            linkify=dict(viewname="inventory:inventory_detail", args=[tables.A('inventory__pk')]))
    inventory__part__name = Column(verbose_name='Part',
            linkify=dict(viewname="parts:parts_detail", args=[tables.A('inventory__part__pk')]))
    config_type = Column(verbose_name='Type')
    configuration_date = DateColumn(verbose_name='Event Date', format='Y-m-d',
            linkify=dict(viewname="exports:configconst", args=[tables.A('pk')])
            )
    user_approver__all__name = ManyToManyColumn(verbose_name='Approvers', accessor='user_approver', transform=lambda x: x.name, default='')
    user_draft__all__name = ManyToManyColumn(verbose_name='Reviewers', accessor='user_draft', transform=lambda x: x.name, default='')

    config_values__names = ManyToManyColumn(verbose_name='Config/Constant Names',
            accessor='config_values', transform=lambda x: x.config_name)
    config_values__notes = ManyToManyColumn(verbose_name='Config/Constant Notes',
            accessor='config_values', transform=lambda x: format_html('<b>{}:</b> [{}]<br>'.format(x.config_name,x.notes)) if x.notes else '', separator='\n')

    detail = Column(verbose_name='ConfigEvent Note', accessor='detail')
    created_at = DateTimeColumn(verbose_name='Date Entered', accessor='created_at', format='Y-m-d H:i')

