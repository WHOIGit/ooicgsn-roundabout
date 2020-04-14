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

import json
import operator
from functools import reduce
from urllib.parse import unquote

#from django.shortcuts import render, get_object_or_404
#from django.template.defaultfilters import register
#from django.urls import reverse, reverse_lazy
#from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, QueryDict
#from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
#from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.db.models import Q
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

import django_tables2 as tables
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

from roundabout.inventory.models import Inventory
from roundabout.parts.models import Part
from roundabout.assemblies.models import Assembly
from roundabout.builds.models import Build

from .tables import InventoryTable, PartTable, BuildTable, AssemblyTable, UDF_FIELDS, UDF_Column


def searchbar_redirect(request):
    # TODO probably js based but: make the default model to search on match the page/app.
    print('SEARCHBAR: ',request.GET)
    model = request.GET['model']
    url = 'search:'+model
    resp = redirect(url)

    query = request.GET['query']
    if query:
        if model=='inventory':      get = '?f=.0.part__name&f=.0.serial_number&f=.0.revision__note&f=.0.location__name&l=.0.icontains&q=.0.{query}'
        elif model=='part':         get = '?f=.0.part_number&f=.0.name&l=.0.icontains&q=.0.{query}'
        elif model == 'build':      get = '?f=.0.build_number&f=.0.assembly__name&f=.0.assembly__assembly_type__name&f=.0.assembly__description&f=.0.build_notes&f=.0.detail&f=.0.location__name&l=.0.icontains&q=.0.{query}'
        elif model == 'assembly':   get = '?f=.0.assembly_number&f=.0.name&f=.0.assembly_type__name&f=.0.description&l=.0.icontains&q=.0.{query}'
        get = get.format(query=query)
        resp['Location'] += get
    return resp


class GenericSearchTableView(LoginRequiredMixin,ExportMixin,SingleTableView):
    model = None
    table_class = None
    #context_object_name = 'query_objs'
    template_name = 'search/adv_search.html'
    exclude_columns = []

    STR_LOOKUPS = ['contains', 'icontains', 'exact', 'iexact',
                   'startswith', 'istartswith', 'endswith', 'iendswith', 'regex', 'iregex']
    NUM_LOOKUPS = ['exact', 'gt', 'gte', 'lt', 'lte', 'range']
    DATE_LOOKUPS= ['date', 'year', 'iso_year', 'month', 'day', 'week', 'week_day',
                   'quarter', 'time', 'hour', 'minute', 'second'] + NUM_LOOKUPS + ['date_lookup']
    ITER_LOOKUPS = ['in']
    BOOL_LOOKUPS = ['exact','iexact','bool_lookup']
    # TODO bool_lookup and date_lookup is a hack. Instead, add these as a dict to context and have legal_lookups hold the keys to appropriate context dict


    def get_search_cards(self):
        GET = self.request.GET
        fields = GET.getlist('f')
        lookups = GET.getlist('l')
        queries = GET.getlist('q')
        negas = GET.getlist('n')

        fields = [unquote(f).split('.',2)+['f'] for f in fields]
        lookups = [unquote(l).split('.',2)+['l'] for l in lookups]
        queries = [unquote(q).split('.',2)+['q'] for q in queries]
        negas = [unquote(n).split('.',2)+['n'] for n in negas]

        all_things = fields+lookups+queries+negas

        cards = []
        card_IDs = sorted(set([c for c,r,v,t in all_things]))
        for card_id in card_IDs:
            card_things = [(c,r,v,t) for c,r,v,t in all_things if c==card_id]
            row_IDs = sorted(set([r for c,r,v,t in card_things]))
            rows = []
            for row_id in row_IDs:
                row_items = [(v,t) for c,r,v,t in card_things if r==row_id]
                fields = [v for v,t in row_items if t=='f']
                lookup = [v for v,t in row_items if t=='l']
                query = [v for v,t in row_items if t=='q']
                nega = [v for v,t in row_items if t=='n']
                # TODO VERIFICATION response
                try:
                    assert len(fields) >=1
                    assert len(lookup)==1
                    assert len(query)==1 and query[0]
                    assert len(nega) <= 1
                except AssertionError:
                    continue
                row = dict(#row_id=row_id,
                           fields=fields,
                           lookup=lookup[0],
                           query=query[0],
                           nega=bool(nega),
                           multi=len(fields)>1)
                rows.append(row)
            cards.append(dict(card_id=card_id, rows=rows)) # TODO placeholder to add more values to given card

        return cards

    def get_queryset(self):
        cards = self.get_search_cards()

        final_Qs = []
        for card in cards:
            print('CARD:', card)
            card_Qs = []
            for row in card['rows']:
                Q_kwargs = []
                for field in row['fields']:
                    # TODO: field x lookup VALIDATION HERE
                    # eg: Q(<field>__<lookup>=<query>) where eg: field = "part__part_number" and lookup = "icontains"
                    #Q_string = 'Q({field}__{lookup}={query})'.format(**row, field=field)
                    Q_kwarg = {'{field}__{lookup}'.format(field=field, lookup=row['lookup']): row['query']}
                    Q_kwargs.append(Q_kwarg)

                if len(Q_kwargs) > 1:
                    row_Q = reduce(operator.or_,[Q(**Q_kwarg) for Q_kwarg in Q_kwargs])
                elif Q_kwargs:
                    row_Q = Q(**Q_kwargs[0])
                else:
                    row_Q = None
                if row['nega'] and row_Q:
                    row_Q = operator.inv(row_Q)
                if row_Q:
                    card_Qs.append(row_Q)
                # ROW DONE
            if len(card_Qs) > 1:
                card_Q = operator.and_(*card_Qs)
            elif card_Qs:
                card_Q = card_Qs[0]
            else:
                card_Q = None
            if card_Q:
                final_Qs.append(card_Q)
            # CARD DONE

        if len(final_Qs) > 1:
            final_Q = reduce(operator.or_,final_Qs)
        elif final_Qs:
            final_Q = final_Qs[0]
        else:
            final_Q = None

        if final_Q:
            return self.model.objects.filter(final_Q).distinct()
        else:
            #return self.model.objects.none()
            return self.model.objects.all()


    def get_context_data(self, **kwargs):
        context = super(GenericSearchTableView, self).get_context_data(**kwargs)

        # Cards to initiate previous columns
        cards = self.get_search_cards()
        context['prev_cards'] = json.dumps(cards)
        context['model'] = self.model.__name__

        avail_lookups = [dict(value='icontains',text='Contains'),
                         dict(value='exact',    text='Exact'),
                         dict(value='gte',      text='>='),
                         dict(value='lte',      text='<='),]
        context['avail_lookups'] = json.dumps(avail_lookups)

        lcats = dict(
            STR_LOOKUPS  = ['contains', 'exact', 'startswith', 'endswith', 'regex',
                          'icontains','iexact','istartswith','iendswith','iregex'],
            NUM_LOOKUPS  = ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
            DATE_LOOKUPS = ['date', 'year', 'iso_year', 'month', 'day', 'week',
                           'week_day', 'quarter', 'time', 'hour', 'minute', 'second'] +
                           ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
            ITER_LOOKUPS = ['in'],
            BOOL_LOOKUPS = ['exact','iexact'], )
        context['lookup_categories'] = json.dumps(lcats)

        context['avail_fields'] = json.dumps(self.get_avail_fields())

        # Setting default shown columns, only columns who which have any data* in them will show
        # * well actually it looks at the Part of the inventory and keeps all UDF's that appear there for the whole table.
        context['table'].set_column_default_show(self.get_table_data())

        return context

    def get_avail_fields(self):
        # default, this should be overwritten by non-generic search class views
        avail_fields = [dict(value="id", text="Database ID", legal_lookups=['exact'])]
        return avail_fields

    def get_table_kwargs(self, field_exceptions=[]):
        extra_cols = []

        queried_fields = []
        udfname_queries = []
        udfvalue_queries = []

        for card in self.get_search_cards():
            for row in card['rows']:
                for field in row['fields']:
                    if field not in field_exceptions:
                        queried_fields.append(field)
        queried_fields = set(queried_fields)

        for field in self.get_avail_fields():
            if field['value'] is not None \
               and not field['text'].startswith('UDF') \
               and field['value'] not in self.table_class.Meta.fields:
                if field['value'] in queried_fields:
                    safename = 'searchcol-{}'.format(field['value'])
                else:
                    safename = 'extracol-{}'.format(field['value'])

                if 'date_lookup' in field['legal_lookups']:
                    col = tables.DateTimeColumn(verbose_name=field['text'], accessor=field['value'])
                elif 'bool_lookup' in field['legal_lookups']:
                    col = tables.BooleanColumn(verbose_name=field['text'], accessor=field['value'])
                else:
                    col = tables.Column(verbose_name=field['text'], accessor=field['value'])

                extra_cols.append( (safename,col) )

        # exclude cols from download
        try: self.exclude_columns = self.request.GET.get('excluded_columns').split(',')
        except AttributeError: self.exclude_columns = []
        return {'extra_columns':extra_cols}


class InventoryTableView(GenericSearchTableView):
    model = Inventory
    table_class = InventoryTable

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs(field_exceptions=['fieldvalues__field__field_name','fieldvalues__field_value'])

        udfname_queries = []
        udfvalue_queries = []
        for card in self.get_search_cards():
            for row in card['rows']:
                if 'fieldvalues__field__field_name' in row['fields']:
                    udfname_queries.append(row['query'])  # capture this row's query
                #elif 'fieldvalues__field_value' in row['fields']:
                #    udfvalue_queries.append(row['query']) # TODO show all UDF that match this ?? How??

        # UDF Cols: these have to be added before the table is made
        # since we don't yet know which UDF columns will have data
        # see table_class.set_column_default_show for logics
        for udf in UDF_FIELDS:
            safename =  UDF_Column.prefix+'{:03}'.format(udf.id)
            if any([qry.lower() in udf.field_name.lower() for qry in udfname_queries]):
                safename = 'searchcol-'+safename
            kwargs['extra_columns'].append( (safename, UDF_Column(udf)) )

        return kwargs

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.exclude(location__root_type='Trash')
        fetch_me = ['fieldvalues','fieldvalues__field','part','location','revision']
        qs = qs.prefetch_related(*fetch_me)
        return qs

    def get_avail_fields(self):
        avail_fields = [dict(value="part__name",              text="Name", legal_lookups=self.STR_LOOKUPS),
                        dict(value="serial_number",  text="Serial Number", legal_lookups=self.STR_LOOKUPS),
                        dict(value="build__assembly__name",  text="Build", legal_lookups=self.STR_LOOKUPS),
                        dict(value="revision__note",          text="Note", legal_lookups=self.STR_LOOKUPS),
                        dict(value="created_at",      text="Date Created", legal_lookups=self.DATE_LOOKUPS),
                        dict(value="updated_at",     text="Date Modified", legal_lookups=self.DATE_LOOKUPS),

                        dict(value=None, text="--Part--", disabled=True),
                        dict(value="part__part_number",        text="Part Number", legal_lookups=self.STR_LOOKUPS),
                        dict(value="part__part_type__name",    text="Part Type", legal_lookups=self.STR_LOOKUPS),
                        dict(value="part__unit_cost",          text="Unit Cost", legal_lookups=self.NUM_LOOKUPS),
                        dict(value="part__refurbishment_cost", text="Refurb Cost", legal_lookups=self.NUM_LOOKUPS),

                        dict(value=None, text="--Location--", disabled=True),
                        dict(value="location__name",          text="Name", legal_lookups=self.STR_LOOKUPS),
                        dict(value="location__location_type", text="Location Type", legal_lookups=self.STR_LOOKUPS),
                        dict(value="location__root_type",     text="Location Root", legal_lookups=self.STR_LOOKUPS),

                        dict(value=None, text="--User-Defined-Fields--", disabled=True),
                        dict(value="fieldvalues__field__field_name", text="UDF Name", legal_lookups=self.STR_LOOKUPS),
                        dict(value="fieldvalues__field_value",       text="UDF Value",
                             legal_lookups=self.STR_LOOKUPS+self.NUM_LOOKUPS+self.ITER_LOOKUPS),]
        return avail_fields

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PartTableView(GenericSearchTableView):
    model = Part
    table_class = PartTable

    def get_avail_fields(self):
        avail_fields = [dict(value="name",                      text="Name", legal_lookups=self.STR_LOOKUPS),
                        dict(value="part_number",        text="Part Number", legal_lookups=self.STR_LOOKUPS),
                        dict(value="part_type__name",      text="Part Type", legal_lookups=self.STR_LOOKUPS),
                        dict(value="unit_cost",            text="Unit Cost", legal_lookups=self.NUM_LOOKUPS),
                        dict(value="refurbishment_cost", text="Refurb Cost", legal_lookups=self.NUM_LOOKUPS),
                        dict(value="note",                      text="Note", legal_lookups=self.STR_LOOKUPS),

                        dict(value=None, text="--User-Defined-Fields--", disabled=True),
                        dict(value="user_defined_fields__field_name", text="UDF Name", legal_lookups=self.STR_LOOKUPS),]
        return avail_fields

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs(field_exceptions=['user_defined_fields__field_name'])

        udfname_queries = []
        cards = self.get_search_cards()
        for card in cards:
            for row in card['rows']:
                if 'user_defined_fields__field_name' in row['fields']:
                    udfname_queries.append(row['query'])  # capture this row's query

        # UDF Cols: these have to be added before the table is made
        # since we don't yet know which UDF columns will have data
        # see table_class.set_column_default_show for logics
        for udf in UDF_FIELDS:
            safename =  UDF_Column.prefix+'{:03}'.format(udf.id)
            if any([qry.lower() in udf.field_name.lower() for qry in udfname_queries]):
                safename = 'searchcol-'+safename
            kwargs['extra_columns'].append( (safename, UDF_Column(udf)) )

        return kwargs

    def get_queryset(self):
        qs = super().get_queryset()
        fetch_me = ['user_defined_fields','part_type']
        qs = qs.prefetch_related(*fetch_me)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class BuildTableView(GenericSearchTableView):
    model = Build
    table_class = BuildTable

    def get_avail_fields(self):
        avail_fields = [dict(value="assembly__name",                text="Name", legal_lookups=self.STR_LOOKUPS),
                        dict(value="build_number",          text="Build Number", legal_lookups=self.STR_LOOKUPS),
                        dict(value="assembly__assembly_type__name", text="Type", legal_lookups=self.STR_LOOKUPS),
                        dict(value="assembly__description",  text="Description", legal_lookups=self.STR_LOOKUPS),
                        dict(value="build_notes",                  text="Notes", legal_lookups=self.STR_LOOKUPS),
                        dict(value="detail",                      text="Detail", legal_lookups=self.STR_LOOKUPS),
                        dict(value="is_deployed",           text="is-deployed?", legal_lookups=self.BOOL_LOOKUPS),
                        dict(value="time_at_sea",            text="Time at Sea", legal_lookups=self.NUM_LOOKUPS),
                        dict(value="flag",                   text="is-flagged?", legal_lookups=self.BOOL_LOOKUPS),
                        dict(value="created_at",            text="Date Created", legal_lookups=self.DATE_LOOKUPS),
                        dict(value="updated_at",           text="Date Modified", legal_lookups=self.DATE_LOOKUPS),

                        dict(value=None, text="--Location--", disabled=True),
                        dict(value="location__name",          text="Name", legal_lookups=self.STR_LOOKUPS),
                        dict(value="location__location_type", text="Type", legal_lookups=self.STR_LOOKUPS),
                        dict(value="location__root_type",     text="Root", legal_lookups=self.STR_LOOKUPS),]
        return avail_fields

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AssemblyTableView(GenericSearchTableView):
    model = Assembly
    table_class = AssemblyTable

    def get_avail_fields(self):
        avail_fields = [dict(value="name",                text="Name", legal_lookups=self.STR_LOOKUPS),
                        dict(value="assembly_number",   text="Number", legal_lookups=self.STR_LOOKUPS),
                        dict(value="assembly_type__name", text="Type", legal_lookups=self.STR_LOOKUPS),
                        dict(value="description",  text="Description", legal_lookups=self.STR_LOOKUPS),
                        ]
        return avail_fields

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
