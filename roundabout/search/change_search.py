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
from roundabout.configs_constants.models import ConfigEvent, ConfigNameEvent, ConstDefaultEvent, ConfigDefaultEvent, ConfigValue
from roundabout.inventory.models import Action, DeploymentAction, Inventory, InventoryDeployment
from roundabout.parts.models import Part
from roundabout.assemblies.models import AssemblyPart
from roundabout.users.models import User
from roundabout.search.tables import trunc_render, ActionTable

## === TABLES === ##

class ChangeTableBase(tables2.Table):
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        attrs = {'style': 'display: block; overflow-x: auto;'}
        model = None
        title = None


class CalChangeTable(ChangeTableBase):
    class Meta(ChangeTableBase.Meta):
        model = CalibrationEvent
        title = 'Calibration Events'
    inventory__serial_number = Column(verbose_name='Inventory', linkify=dict(viewname="inventory:inventory_detail",
                                                                             args=[tables2.A('inventory__pk')]))
    value_names = ManyToManyColumn(verbose_name='Coefficient Names', accessor='coefficient_value_sets',
                                   transform=lambda x: x.coefficient_name)

class ConfConsChangeTable(ChangeTableBase):
    class Meta(ChangeTableBase.Meta):
        model = ConfigEvent
        title = 'Configuration/Constant Events'
    inventory__serial_number = Column(verbose_name='Inventory', linkify=dict(viewname="inventory:inventory_detail", args=[tables2.A('inventory__pk')]))
    value_names = ManyToManyColumn(verbose_name='Config/Constant Names', accessor='config_values', transform=lambda x: x.config_name)

class ConfChangeActionTable(ChangeTableBase):
    class Meta(ChangeTableBase.Meta):
        model = Action
        title = 'Actions'
        fields = ['object_type', 'object', 'action_type', 'user', 'created_at', 'detail', 'data']
    object = Column(verbose_name='Associated Object', accessor='object_type')

    def render_user(self,value):
        return value.name or value.username

    def render_detail(self,value):
        return trunc_render()(value)
    def value_detail(self,value):
        return value

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

    render_object = ActionTable.render_object

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
              ConfConsChangeTable,
              ]

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        # disable ColumnShiftTable behavior
        for table in self.tables:
            if issubclass(table,ColumnShiftTable):
                table.shift_table_column = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model'] = 'change'
        for table in context['tables']:
            table.attrs['title'] = table.Meta.title if hasattr(table.Meta,'title') else table.__name__.replace('Table','s')
        return context

    def get_tables_data(self):
        if 'q' in self.request.GET:
            query = self.request.GET.get('q')
        else: # defaults
            query = ''

        config_event_matches = ConfigValue.objects.filter(config_value__exact=query).values_list('config_event__pk',flat=True)
        conf_Q = Q(pk__in=config_event_matches)

        conf_action_Q = Q(config_event__pk__in=config_event_matches)

        qs_list = []
        for table in self.tables:
            if table.Meta.model == Action:
                action_qs = Action.objects.filter(conf_action_Q)
                qs_list.append(action_qs)
            else:
                action_qs = table.Meta.model.objects.filter(conf_Q)
                qs_list.append(action_qs)

        return qs_list

    def get(self, request, *args, **kwargs):
        initial = dict(q='')
        if 'q' in request.GET:
            form = self.form_class(request.GET)
        else:
            form = self.form_class(initial)
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)
