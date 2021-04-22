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

import django_tables2 as tables2
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from django.views.generic import TemplateView
from django_tables2.columns import Column, DateTimeColumn, ManyToManyColumn, BooleanColumn
from django_tables2_column_shifter.tables import ColumnShiftTable

from roundabout.builds.models import BuildAction, Build, Deployment
from roundabout.calibrations.models import CalibrationEvent, CoefficientNameEvent
from roundabout.configs_constants.models import ConfigEvent, ConfigNameEvent, ConstDefaultEvent, ConfigDefaultEvent, ConfigValue, ConfigName
from roundabout.inventory.models import Action, DeploymentAction, Inventory, InventoryDeployment
from roundabout.parts.models import Part
from roundabout.assemblies.models import AssemblyPart
from roundabout.users.models import User
from roundabout.search.tables import trunc_render, ActionTable

## === TABLES === ##

class CCC_ValueColumn(Column):
    def __init__(self, ccc_name, note=False, **kwargs):
        self.ccc_name = ccc_name
        self.is_note = note
        col_name = '{} note'.format(ccc_name) if note else ccc_name
        super().__init__(accessor='data', verbose_name=col_name, default='',**kwargs)

    def render(self,value):
        key = 'updated_notes' if self.is_note else 'updated_values'
        try: return value[key][self.ccc_name]['to']
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
    created_at = DateTimeColumn(orderable=True)

    def set_column_default_show(self):
        notnote_cols = [col for col in self.sequence if not col.endswith('_note')]
        self.column_default_show = notnote_cols
    def render_user(self,value):
        return value.name or value.username

class ConfChangeActionTable(ChangeTableBase):
    class Meta(ChangeTableBase.Meta):
        title = 'Configuration Change Actions'
        fields = ['created_at', 'action_type', 'inventory', 'config_event', 'config_event__approved', 'user', 'config_event__deployment']  #,'data']
        object_type = Action.CONFEVENT
    created_at = DateTimeColumn(verbose_name='Action Timestamp')
    inventory = Column(verbose_name='Inventory SN', accessor='config_event__inventory',
                linkify=dict(viewname="inventory:inventory_detail", args=[tables2.A('config_event__inventory__pk')]))

    # TODO action history data for when config event gets APPROVED by a user
    # TODO action history data for when config event gets ADDED to DB

    def render_action_type(self,record):
        return '{}: {}'.format(record.object_type,record.action_type)
    '''
    def render_data(self,value):
        template = '"{KEY}" to: {TO}\n{GAP} from: {FROM}\n'
        output_str = ''
        try:
            if 'updated_values' in value:
                #output_str += 'UPDATED VALUES\n'
                for key,val in value['updated_values'].items():
                    to_val,from_val = val['to'],val['from']
                    if len(to_val) > 10: to_val = to_val[:10]+'…'
                    if len(from_val)>10: to_val = from_val[:10]+'…'
                    output_str += template.format(KEY=key,FROM=from_val,TO=to_val,GAP=' '*len(key))
            return mark_safe('<pre>'+output_str[:-1]+'</pre>')
        except:
            return value
    def value_data(self,value):
        return value
    '''

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
    approved = forms.BooleanField(required=False, label='Approved Only')

    def __init__(self, *args, **kwargs):
        default_refdeslist = ConfigValue.objects.filter(config_name__name__exact='Reference Designator').values_list('config_value',flat=True)
        default_refdeslist = sorted(set(default_refdeslist))
        refdeslist = kwargs.pop('data_list', default_refdeslist)
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['q'].widget=ListTextWidget(refdeslist, name='refdeslist')


## === VIEWS === ##

class ChangeSearchView(LoginRequiredMixin, tables2.MultiTableMixin, TemplateView):
    template_name = 'search/form_search_multitable.html'
    form_class = SearchForm
    table_pagination = {"per_page": 10}

    tables = [ConfChangeActionTable,
             # TODO CalibChangeActionTable: needs action_history update.
             #                              needs a way to figure out what CalibEvent falls within a given ref-des
             ]

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

    def get_tables_kwargs(self):
        if 'q' in self.request.GET:
            query = self.request.GET.get('q')
        else: return len(self.tables)*[{}]

        kwargss = []
        for table in self.tables:
            extra_cols = []
            if table.Meta.object_type == Action.CONFEVENT:
                cc_events = ConfigValue.objects.filter(config_value__exact=query).values_list('config_event__pk',flat=True)
                cc_names = ConfigName.objects.filter(config_values__config_event__pk__in=cc_events).values_list('name',flat=True)
                cc_names = sorted(set(cc_names))
                for cc_name in cc_names:
                    safename = cc_name.replace(' ','-')
                    col = safename, CCC_ValueColumn(cc_name)
                    col_note = safename +'_note', CCC_ValueColumn(cc_name, note=True)
                    extra_cols.append(col)
                    extra_cols.append(col_note)
            kwargss.append( {'extra_columns':extra_cols} )
        return kwargss

    def get_tables_data(self):
        if 'q' in self.request.GET:
            query = self.request.GET.get('q')
        else:  # defaults
            return [[]]*len(self.tables)
        approved_only = 'approved' in self.request.GET

        config_event_matches = ConfigValue.objects.filter(config_value__exact=query).values_list('config_event__pk',flat=True)
        if approved_only:
            conf_action_Q = Q(config_event__pk__in=config_event_matches, config_event__approved=True)
        else:
            conf_action_Q = Q(config_event__pk__in=config_event_matches)
        #conf_Q = Q(pk__in=config_event_matches)

        #calib_event_matches = CalibrationEvent.objects.filter(inventory__).values_list('pk',flat=True)
        #calib_action_Q = Q(config_event__pk__in=calib_event_matches)
        #calib_Q = Q(pk__in=calib_event_matches)

        qs_list = []
        for table in self.tables:
            if table.Meta.object_type == Action.CONFEVENT:
                action_qs = Action.objects.filter(conf_action_Q)
                if approved_only:
                    pass # TODO compile Action data to show all approved changes per approval
                qs_list.append(action_qs)
            #elif table.Meta.object_type == Action.CALEVENT:
            #    action_qs = Action.objects.filter(calib_action_Q)
            #    qs_list.append(action_qs)

        return qs_list

    def get_tables(self):
        """
        Return an array of table instances containing data.
        """
        if self.tables is None:
            klass = type(self).__name__
            raise tables2.views.ImproperlyConfigured("No tables were specified. Define {}.tables".format(klass))
        data = self.get_tables_data()
        kwargss = self.get_tables_kwargs()

        if data is None:
            return self.tables

        if len(data) != len(self.tables) != len(kwargss):
            klass = type(self).__name__
            raise tables2.views.ImproperlyConfigured("len({}.tables_data) != len({}.tables)".format(klass, klass))
        return list(Table(data[i],**kwargss[i]) for i, Table in enumerate(self.tables))


