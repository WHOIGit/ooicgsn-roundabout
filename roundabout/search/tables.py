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
from roundabout.builds.models import Build
from roundabout.inventory.models import Inventory
from roundabout.assemblies.models import Assembly
from roundabout.userdefinedfields.models import Field


class UDF_Column(ManyToManyColumn):
    prefix = 'udf-'
    def __init__(self,udf,*args,**kwargs):
        self.udf = udf
        super().__init__(accessor='fieldvalues', verbose_name=udf.field_name, orderable=True, default='',
                         filter=lambda qs: qs.filter(field__id=udf.id, is_current=True))

class OneOfManyColumn(Column):
    def __init__(self, accessor, accessor_field=None, select_one_by='first', wrapper=None, *args, **kwargs):
        self.accessor_field = accessor_field
        self.wrapper = wrapper
        assert select_one_by in ['first','last','count','latest','earliest']
        self.select_one_by = select_one_by
        super().__init__(*args, accessor=accessor, orderable=True, default='', **kwargs)

    def render(self,value):
        if not value.exists():
            return self.default

        many = value.all()
        one_of_many = getattr(many,self.select_one_by)()

        if self.accessor_field is None:
            one_of_many__value = str(one_of_many)
        elif len(self.accessor_field.split('__'))>1:
            breadcrumbs = self.accessor_field.split('__')
            one_of_many__value = getattr(one_of_many,breadcrumbs[0])
            for bc in breadcrumbs[1:]:
                one_of_many__value = getattr(one_of_many__value,bc)
        else:
            one_of_many__value = getattr(one_of_many, self.accessor_field)

        if self.wrapper:
            return self.wrapper(one_of_many__value)
        return one_of_many__value


class SearchTable(ColumnShiftTable):
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        base_shown_cols = []

    def set_column_default_show(self, table_data):
        if not self.Meta.base_shown_cols:
            self.column_default_show = None
        else:
            search_cols = [col for col in self.sequence if col.startswith('searchcol-')]
            extra_cols = [col for col in self.sequence if col.startswith('extracol-')]
            self.column_default_show = self.Meta.base_shown_cols + search_cols

class InvActionTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Inventory
        fields = ['serial_number', 'part__name', 'location__name']
        base_shown_cols = fields
        action_accessors = ['latest_action__action_type', 'latest_action__user__name', 'latest_action__created_at', 'latest_action__detail']

    serial_number = Column(verbose_name='Serial Number',
              linkify=dict(viewname="inventory:inventory_detail", args=[tables.A('pk')]))
    location__name = Column(verbose_name='Location')

    latest_action__action_type = OneOfManyColumn(accessor='action', verbose_name='Latest Action', accessor_field='action_type', wrapper=str)
    latest_action__user__name = OneOfManyColumn(accessor='action', verbose_name='Latest Action: User', accessor_field='user__name')
    latest_action__created_at = OneOfManyColumn(accessor='action', verbose_name='Latest Action: Time', accessor_field='created_at')
    latest_action__detail = OneOfManyColumn(accessor='action', verbose_name='Latest Action: Details', accessor_field='detail', wrapper=mark_safe)


class InventoryTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Inventory
        fields = ['serial_number','part__name','location__name','revision__note']
        base_shown_cols = ['serial_number', 'part__name', 'location__name']
        action_accessors = ['latest_action__action_type', 'latest_action__user__name', 'latest_action__created_at', 'latest_action__detail']
        udf_accessors = ['fieldvalues__field__field_name','fieldvalues__field_value']

    # default columns
    serial_number = Column(verbose_name='Serial Number',
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

        # Uncomment to (a) show all UDF's with data, (b) remove UDF cols with no data
        # get a list of unique UDF id's present in query-results
        # if an ID is not present, then that UDF column will have zero entries.
        actual_udf_IDs = set(table_data.values_list('fieldvalues__field__id', flat=True))
        udf_boundcols = [bc for bc in self.columns if bc.name.startswith(UDF_Column.prefix)]
        for bound_col in udf_boundcols:                          # for all the table's UDF columns
            if bound_col.column.udf.id in actual_udf_IDs:        # if the id is present, then it has has data
                pass #self.column_default_show.append(bound_col.name)  # and the column should be shown by default
            else:                                                # ELSE
                bound_col.column.visible = False                 # Remove column from the interface, but will exist in export.
                bound_col.column.exclude_from_export = True      # Removes column from the export list!


    def render_serial_number(self, value, record):
        item_url = reverse("inventory:inventory_detail", args=[record.pk])
        html_string = '<a href={}>{}</a>'
        return format_html(html_string, item_url, value)
    def value_serial_number(self,record):
        return record.serial_number

    def render_part(self,record):
        item_url = reverse("parts:parts_detail", args=[record.part.pk])
        name = record.part.friendly_name_display()
        html_string = '{} <a href={}>➤</a>'
        return format_html(html_string,name, item_url)
    def value_part(self,record):
        return record.part.friendly_name_display()

    def render_revision__note(self,value):
        return mark_safe(value)
    def value_revision__note(self,record):
        return record.revision.note


class PartTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Part
        fields = ["part_number", 'name', 'part_type__name','inventory__count']
        base_shown_cols = fields

    part_number = tables.Column(verbose_name='Part Number',
                   linkify=dict(viewname='parts:parts_detail',args=[tables.A('pk')]))
    part_type__name = tables.Column(verbose_name='Type')
    inventory__count = tables.Column(empty_values=())

    def render_name(self,record):
        return record.friendly_name_display()

    #def render_inventory_count(self,record):
    #    return record.get_part_inventory_count()
    #def order_inventory_count(self, queryset, is_ascending):
    #    queryset = queryset.annotate(count=Count('inventory'))\
    #                       .order_by(("" if is_ascending else "-")+'count')
    #    return queryset, True

    def set_column_default_show(self,table_data):
        search_cols = [col for col in self.sequence if col.startswith('searchcol-')]
        extra_cols = [col for col in self.sequence if col.startswith('extracol-')]
        udf_cols = [col for col in self.sequence if col.startswith(UDF_Column.prefix) \
                                                 or col.startswith('searchcol-'+UDF_Column.prefix)]
        self.column_default_show = self.Meta.base_shown_cols + search_cols

        # Uncomment to (a) show all UDF's with data, (b) remove UDF cols with no data
        # get a list of unique UDF id's present in query-results
        # if an ID is not present, then that UDF column will have zero entries.
        actual_udf_IDs = set(table_data.values_list('fieldvalues__field__id', flat=True))
        udf_boundcols = [bc for bc in self.columns if bc.name.startswith(UDF_Column.prefix)]
        for bound_col in udf_boundcols:                          # for all the table's UDF columns
            if bound_col.column.udf.id in actual_udf_IDs:        # if the id is present, then it has has data
                pass #self.column_default_show.append(bound_col.name)  # and the column should be shown by default
            else:                                                # ELSE
                bound_col.column.visible = False                 # Remove column from the interface, but will exist in export.
                bound_col.column.exclude_from_export = True      # Removes column from the export list!

class BuildTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Build
        fields = ['build','assembly__name','build_number','assembly__assembly_type__name','location__name','is_deployed','time_at_sea']
        base_shown_cols = ['build','assembly__assembly_type__name','location__name','is_deployed','time_at_sea']
        action_accessors = ['latest_action__action_type', 'latest_action__user__name', 'latest_action__created_at','latest_action__detail']

    build=tables.Column(empty_values=(), attrs={"th": {"style": "white-space:nowrap;"}})
    location__name = tables.Column(verbose_name='Location', accessor='location__name')
    assembly__assembly_type__name = tables.Column(verbose_name='Type')

    latest_action__action_type = OneOfManyColumn(accessor='deployment_actions', verbose_name='Latest Action')
    latest_action__user__name = OneOfManyColumn(accessor='deployment_actions', verbose_name='Latest Action: User', accessor_field='user__name')
    latest_action__created_at = OneOfManyColumn(accessor='deployment_actions', verbose_name='Latest Action: Time', accessor_field='created_at')
    latest_action__detail = OneOfManyColumn(accessor='deployment_actions', verbose_name='Latest Action: Details', accessor_field='detail')

    def render_build(self, record):
        item_url = reverse("builds:builds_detail", args=[record.pk])
        html_string = '<a href={}>{}-{}</a>'.format(item_url, record.assembly.assembly_number, record.build_number.replace('Build ',''))
        return format_html(html_string)
    def value_build(self,record):
        return '{}-{}'.format(record.assembly.assembly_number, record.build_number.replace('Build ',''))


class AssemblyTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Assembly
        fields = ['assembly_number', 'name', 'assembly_type__name', 'description']
        base_shown_cols = ['assembly_number', 'name', 'assembly_type__name']

    assembly_number = tables.Column(linkify=dict(viewname='assemblies:assembly_detail',args=[tables.A('pk')]))


