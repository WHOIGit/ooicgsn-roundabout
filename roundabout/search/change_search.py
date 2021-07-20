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
from itertools import chain

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q,F
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from django.views.generic import TemplateView
from django_tables2.columns import Column, DateTimeColumn, ManyToManyColumn, BooleanColumn
from django_tables2_column_shifter.tables import ColumnShiftTable
from django_tables2.views import ImproperlyConfigured
from django_tables2 import MultiTableMixin, A

from roundabout.builds.models import BuildAction, Build, Deployment
from roundabout.calibrations.models import CalibrationEvent, CoefficientValueSet, CoefficientName
from roundabout.configs_constants.models import ConfigEvent, ConfigValue, ConfigName
from roundabout.inventory.models import Action, DeploymentAction, Inventory, InventoryDeployment
from roundabout.ooi_ci_tools.models import ReferenceDesignator
from roundabout.search.tables import trunc_render
from roundabout.search.mixins import MultiExportMixin
from roundabout.exports.views import ExportDeployments

## === TABLES === ##

class ActionData_ValueUpdate_Column(Column):
    def __init__(self, value_name, note=False, **kwargs):
        self.value_name = value_name
        self.is_note = note
        super().__init__(accessor='data', default='', **kwargs)

    def render(self,value):
        key = 'updated_notes' if self.is_note else 'updated_values'
        try: return value[key][self.value_name]['to']
        except KeyError:
            print(value)
            return ''


class ChangeTableBase(ColumnShiftTable):
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        attrs = {'style': 'display: block; overflow-x: auto;'}
        model = Action
        orderable = False
        fields = ['created_at','action_type','user']
        title = None
    created_at = DateTimeColumn(verbose_name='Action Timestamp', orderable=True)

    def set_column_default_show(self):
        notnote_cols = [col for col in self.sequence if not col.endswith('_note') and not col.endswith('__approved')]
        self.column_default_show = notnote_cols
    def render_user(self,value):
        return value.name or value.username

class CalibChangeActionTable(ChangeTableBase):
    class Meta(ChangeTableBase.Meta):
        title = 'CalibrationEvent History'
        fields = ['created_at', 'action_type', 'inventory', 'calibration_event', 'calibration_event__approved', 'user']
        object_type = Action.CALEVENT
    inventory = Column(verbose_name='Inventory SN', accessor='calibration_event__inventory',
                linkify=dict(viewname="inventory:inventory_detail", args=[A('calibration_event__inventory__pk')]))


class ConfChangeActionTable(ChangeTableBase):
    class Meta(ChangeTableBase.Meta):
        title = 'ConfigurationEvent History'
        fields = ['created_at', 'action_type', 'inventory', 'config_event', 'config_event__approved', 'user', 'config_event__deployment']
        object_type = Action.CONFEVENT
    inventory = Column(verbose_name='Inventory SN', accessor='config_event__inventory',
                linkify=dict(viewname="inventory:inventory_detail", args=[A('config_event__inventory__pk')]))


class DeployementChangeActionTable(ChangeTableBase):
    class Meta(ChangeTableBase.Meta):
        title = 'Deployment History'
        fields = ['created_at', 'action_type', 'build', 'user']
        object_type = Action.DEPLOYMENT
    build = Column(verbose_name='Build', accessor='build',
            linkify=dict(viewname="builds:builds_detail", args=[A('build__pk')]))


# ========= FORM STUFF ========= #

class ListTextWidget(forms.TextInput):
    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.attrs.update({'list':'list__{}'.format(self._name)})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = '<datalist id="list__{}">'.format(self._name)
        for item in self._list:
            data_list += '<option value="{}">'.format(item)
        data_list += '</datalist>'
        return text_html + data_list


class SearchForm(forms.Form):
    q = forms.CharField(required=True, label='Reference Designator')

    def __init__(self, *args, **kwargs):
        default_refdeslist = ReferenceDesignator.objects.all().values_list('refdes_name',flat=True)
        #default_refdeslist = ConfigValue.objects.filter(config_name__name__exact='Reference Designator').values_list('config_value',flat=True)
        default_refdeslist = sorted(set(default_refdeslist))
        refdeslist = kwargs.pop('data_list', default_refdeslist)
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['q'].widget=ListTextWidget(refdeslist, name='refdeslist')


## === VIEWS === ##

class ChangeSearchView(LoginRequiredMixin, MultiTableMixin, MultiExportMixin, TemplateView):
    template_name = 'search/form_search_multitable.html'
    form_class = SearchForm
    table_pagination = {"per_page": 10}

    tables = [CalibChangeActionTable,  # needs a way to figure out what CalibEvent falls within a given ref-des
              ConfChangeActionTable,
              DeployementChangeActionTable,
             ]
    export_name = '{table}__{refdes}'

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        # enable ColumnShiftTable behavior
        for table in self.tables:
            if issubclass(table,ColumnShiftTable):
                table.shift_table_column = True

    def get(self, request, *args, **kwargs):
        initial = dict(q='')
        if 'q' in request.GET:
            form = self.form_class(request.GET)
        else:
            form = self.form_class(initial)
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # <-- get_tables, get_tables_data, get_tables_kwargs happens here!
        context['model'] = 'change'
        for table in context['tables']:
            table.attrs['title'] = table.Meta.title if hasattr(table.Meta,'title') else table.__name__.replace('Table','s')
            table.set_column_default_show()
        return context

    def get_tables(self):
        """
        Return an array of table instances containing data.
        """
        if self.tables is None:
            klass = type(self).__name__
            raise ImproperlyConfigured("No tables were specified. Define {}.tables".format(klass))
        data = self.get_tables_data()
        kwargss = self.get_tables_kwargs()

        if data is None:
            return self.tables

        if len(data) != len(self.tables) != len(kwargss):
            klass = type(self).__name__
            raise ImproperlyConfigured("len({}.tables_data) != len({}.tables)".format(klass, klass))
        return list(Table(data[i],**kwargss[i]) for i, Table in enumerate(self.tables))

    def get_tables_data(self):
        if 'q' in self.request.GET:
            query = self.request.GET.get('q')
        else:  # defaults
            return len(self.tables)*[[]]

        qs_list = []
        for table in self.tables:
            if table.Meta.object_type == Action.CONFEVENT:
                action_qs = Action.objects.prefetch_related('config_event__inventory__assembly_part__reference_designator').\
                    filter(config_event__inventory__assembly_part__reference_designator__refdes_name=query)
                qs_list.append(action_qs)
            elif table.Meta.object_type == Action.CALEVENT:
                action_qs = Action.objects.prefetch_related('calibration_event__inventory__assembly_part__reference_designator').\
                    filter(calibration_event__inventory__assembly_part__reference_designator__refdes_name=query)
                qs_list.append(action_qs)
            elif table.Meta.object_type == Action.DEPLOYMENT:
                action_qs = Action.objects.prefetch_related('deployment__inventory_deployments__assembly_part__reference_designator').\
                    filter(deployment__inventory_deployments__assembly_part__reference_designator__refdes_name=query, data__isnull=False)
                qs_list.append(action_qs)

        return qs_list

    def get_tables_kwargs(self):
        if 'q' in self.request.GET:
            query = self.request.GET.get('q')
        else:
            return len(self.tables)*[{}]

        kwargss = []
        for table in self.tables:
            extra_cols = []
            verbose_names = {}
            if table.Meta.object_type == Action.CONFEVENT:
                value_names = ConfigName.objects.prefetch_related('config_values__config_event__inventory__assembly_part__reference_designator').\
                    filter(config_values__config_event__inventory__assembly_part__reference_designator__refdes_name=query).values_list('name',flat=True)
            elif table.Meta.object_type == Action.CALEVENT:
                value_names = CoefficientName.objects.prefetch_related('coefficient_value_sets__calibration_event__inventory__assembly_part__reference_designator').\
                    filter(coefficient_value_sets__calibration_event__inventory__assembly_part__reference_designator__refdes_name=query).values_list('calibration_name',flat=True)
            elif table.Meta.object_type == Action.DEPLOYMENT:
                value_names = [a for h,a in ExportDeployments.header_att if a]
                verbose_names = {a:h for h,a in ExportDeployments.header_att if a}
            else: value_names = []

            value_names = sorted(set(value_names))
            for value_name in value_names:
                safename = value_name.replace(' ','-')
                verbose_name = verbose_names[value_name] if value_name in verbose_names else value_name
                col = safename, ActionData_ValueUpdate_Column(value_name, verbose_name=verbose_name)
                extra_cols.append(col)
                if table.Meta.object_type in [Action.CONFEVENT,Action.CALEVENT]:
                    verbose_name = '{} note'.format(verbose_name)
                    col_note = safename+'_note', ActionData_ValueUpdate_Column(value_name, verbose_name=verbose_name, note=True)
                    extra_cols.append(col_note)

            kwargss.append( {'extra_columns':extra_cols} )
        return kwargss

    def get_export_filename(self, export_format):
        idx = self.request.GET.get(self.export_trigger_param_table)
        refdes = self.request.GET.get('q')
        table = self.get_tables()[int(idx)]
        title = table.Meta.title
        title = title.lower().replace(' ','_')

        export_name = self.export_name.format(table=title,refdes=refdes)
        return "{}.{}".format(export_name, export_format)

