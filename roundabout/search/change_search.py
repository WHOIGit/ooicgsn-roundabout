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
from roundabout.search.tables import trunc_render
from roundabout.search.mixins import MultiExportMixin

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
        notnote_cols = [col for col in self.sequence if not col.endswith('_note') and not col.endswith('__approved')]
        self.column_default_show = notnote_cols
    def render_user(self,value):
        return value.name or value.username

class CalibChangeActionTable(ChangeTableBase):
    class Meta(ChangeTableBase.Meta):
        title = 'CalibrationEvent History'
        fields = ['created_at', 'action_type', 'inventory', 'calibration_event', 'calibration_event__approved', 'user']
        object_type = Action.CALEVENT
    created_at = DateTimeColumn(verbose_name='Action Timestamp')
    inventory = Column(verbose_name='Inventory SN', accessor='calibration_event__inventory',
                linkify=dict(viewname="inventory:inventory_detail", args=[A('calibration_event__inventory__pk')]))


class ConfChangeActionTable(ChangeTableBase):
    class Meta(ChangeTableBase.Meta):
        title = 'ConfigurationEvent History'
        fields = ['created_at', 'action_type', 'inventory', 'config_event', 'config_event__approved', 'user', 'config_event__deployment']
        object_type = Action.CONFEVENT
    created_at = DateTimeColumn(verbose_name='Action Timestamp')
    inventory = Column(verbose_name='Inventory SN', accessor='config_event__inventory',
                linkify=dict(viewname="inventory:inventory_detail", args=[A('config_event__inventory__pk')]))


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

class ChangeSearchView(LoginRequiredMixin, MultiTableMixin, MultiExportMixin, TemplateView):
    template_name = 'search/form_search_multitable.html'
    form_class = SearchForm
    table_pagination = {"per_page": 10}

    tables = [CalibChangeActionTable,  # needs a way to figure out what CalibEvent falls within a given ref-des
              ConfChangeActionTable,
             ]
    config_event_matches = None
    calib_event_matches = None
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

        # Fetch all ConfigEvents with a matching RefDes field
        self.config_event_matches = ConfigValue.objects.filter(config_value__exact=query).values_list('config_event__pk',flat=True)
        conf_action_Q = Q(config_event__pk__in=self.config_event_matches)

        # Fetch all CalibEvents with an inventory that has ever had a config_event with the matching RefDes (this needs to be further reduced)
        self.calib_event_matches = CalibrationEvent.objects.filter(inventory__config_events__pk__in=self.config_event_matches).values_list('pk',flat=True)
        calib_action_Q = Q(calibration_event__pk__in=self.calib_event_matches)

        # further reduce calib_action_Q: currently calib_action_Q returns ALL CalEvents for a given instrument which has EVER had the matching RefDes is returned.
        config_events = ConfigEvent.objects.filter(pk__in=self.config_event_matches).annotate(date=F('configuration_date'))
        calib_events = CalibrationEvent.objects.filter(pk__in=self.calib_event_matches).annotate(date=F('calibration_date'))
        combined = sorted(chain(config_events, calib_events), key=lambda q: q.date, reverse=True) # sort conf and calib events, most recent first
        groups = {} # group calibrations leading up to any given config/ref-des together, most recent prior to config/ref-des first
        prev_conf = None
        for evt in combined:
            if isinstance(evt,ConfigEvent):
                groups[evt] = []
                prev_conf = evt
            elif prev_conf is not None:
                if prev_conf.inventory == evt.inventory: # make sure the ConfigEvent and CalibEvent actually do refer to the same inventory item
                    groups[prev_conf].append(evt)
        self.calib_event_matches = []
        for key,val in groups.items():
            if val:  # keep just the most recent previous CalibEvent
                self.calib_event_matches.append(val[0].pk)
        calib_action_Q = Q(calibration_event__pk__in=self.calib_event_matches)

        qs_list = []
        for table in self.tables:
            if table.Meta.object_type == Action.CONFEVENT:
                action_qs = Action.objects.filter(conf_action_Q)
                qs_list.append(action_qs)
            elif table.Meta.object_type == Action.CALEVENT:
                action_qs = Action.objects.filter(calib_action_Q)
                qs_list.append(action_qs)

        return qs_list

    def get_tables_kwargs(self):
        if not self.config_event_matches:
            return len(self.tables)*[{}]

        kwargss = []
        for table in self.tables:
            extra_cols = []
            if table.Meta.object_type == Action.CONFEVENT:
                cc_names = ConfigName.objects.filter(config_values__config_event__pk__in=self.config_event_matches).values_list('name',flat=True)
            elif table.Meta.object_type == Action.CALEVENT:
                cc_names = CoefficientName.objects.filter(coefficient_value_sets__calibration_event__pk__in=self.calib_event_matches).values_list('calibration_name',flat=True)
            cc_names = sorted(set(cc_names))
            for cc_name in cc_names:
                safename = cc_name.replace(' ','-')
                col = safename, CCC_ValueColumn(cc_name)
                col_note = safename +'_note', CCC_ValueColumn(cc_name, note=True)
                extra_cols.append(col)
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

