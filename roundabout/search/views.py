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

#from django.urls import reverse, reverse_lazy
from django.utils.html import format_html, mark_safe
#from django.template.defaultfilters import register
#from django.shortcuts import render, get_object_or_404
#from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
#from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, QueryDict
from django.db.models import Q, F, Max, Min, Count
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

import django_tables2 as tables
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

from roundabout.parts.models import Part
from roundabout.builds.models import Build
from roundabout.inventory.models import Inventory
from roundabout.assemblies.models import Assembly
from roundabout.userdefinedfields.models import Field

from .tables import InventoryTable, PartTable, BuildTable, AssemblyTable, UDF_Column


def searchbar_redirect(request):
    model = request.GET.get('model')
    url = 'search:'+model
    resp = redirect(url)

    query = request.GET.get('query')
    if query:
        if model=='inventory':      getstr = '?f=.0.part__name&f=.0.part__friendly_name&f=.0.serial_number&f=.0.old_serial_number&f=.0.location__name&l=.0.icontains&q=.0.{query}'
        elif model=='part':         getstr = '?f=.0.part_number&f=.0.name&f=.0.friendly_name&l=.0.icontains&q=.0.{query}'
        elif model == 'build':      getstr = '?f=.0.build_number&f=.0.assembly__name&f=.0.assembly__assembly_type__name&f=.0.assembly__description&f=.0.build_notes&f=.0.location__name&l=.0.icontains&q=.0.{query}'
        elif model == 'assembly':   getstr = '?f=.0.assembly_number&f=.0.name&f=.0.assembly_type__name&f=.0.description&l=.0.icontains&q=.0.{query}'
        getstr = getstr.format(query=query)
        resp['Location'] += getstr
    return resp


class GenericSearchTableView(LoginRequiredMixin,ExportMixin,SingleTableView):
    model = None
    table_class = None
    context_object_name = 'query_objs'
    template_name = 'search/adv_search.html'
    exclude_columns = []
    query_prefetch = []

    def get_search_cards(self):
        fields = self.request.GET.getlist('f')
        lookups = self.request.GET.getlist('l')
        queries = self.request.GET.getlist('q')
        negas = self.request.GET.getlist('n')

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
                # TODO: VALIDATION HERE?
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
            cards.append(dict(card_id=card_id, rows=rows))
            # TODO placeholder to add more values to given card, like name

        return cards

    def get_queryset(self):
        cards = self.get_search_cards()

        final_Qs = []
        model_objects = self.model.objects
        for card in cards:
            print('CARD:', card)
            card_Qs = []
            for row in card['rows']:
                Q_kwargs = []
                for field in row['fields']:
                    # TODO: field x lookup VALIDATION HERE?
                    # eg: Q(<field>__<lookup>=<query>) where eg: field = "part__part_number" and lookup = "icontains"

                    select_ones = ['__latest__','__last__','__earliest__','__first__']
                    select_one = [s1 for s1 in select_ones if s1 in field]
                    select_one = select_one[0] if select_one else None
                    if not select_one:
                        # default
                        Q_kwarg = {'{field}__{lookup}'.format(field=field, lookup=row['lookup']): row['query']}
                        Q_kwargs.append(Q_kwarg)

                        if field.endswith('__count'):
                            # if field is a count, make sure model_objects is anottated appropriately
                            accessor = field.rsplit('__count',1)[0]
                            annote_obj = {field:Count(accessor)}
                            model_objects = model_objects.annotate(**annote_obj)

                    else:
                        # sometimes we want to query on the latest or first or last value of a list of values.
                        # eg. get inventory where inventory.latest_action.user == 'bob'. This is how we do that.
                        if select_one in ['__latest__','__last__']:
                            annote_func = Max
                        else:
                            annote_func = Min

                        # TODO: consider implementing "is_current" field for actions, similar to UDF.FieldValue.is_current
                        accessor,subfields = field.split(select_one)
                        Accessor = getattr(self.model,accessor).field.model
                        reverse_accessor = getattr(self.model,accessor).field.name
                        fetch_me = ['__'.join(subfields.split('__')[:i]) for i in range(1,len(subfields.split('__')))]
                        fetch_me += [reverse_accessor]

                        all_model_objs = self.model.objects.all().prefetch_related(accessor)
                        all_latest_action_IDs = all_model_objs.annotate(latest_action=annote_func(accessor+'__pk')).values_list('latest_action',flat=True)
                        all_latest_actions = Accessor.objects.filter(pk__in=all_latest_action_IDs).prefetch_related(*fetch_me)
                        matching_latest_actions = all_latest_actions.filter(**{'{}__{}'.format(subfields,row['lookup']):row['query']})
                        matched_model_IDs = matching_latest_actions.values_list(reverse_accessor+'__pk',flat=True)

                        Q_kwarg = {'id__in':matched_model_IDs}
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
                card_Q = reduce(operator.and_,card_Qs)
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
            return model_objects.filter(final_Q).distinct().prefetch_related(*self.query_prefetch)
        else:
            #if there are no search terms
            return model_objects.all().prefetch_related(*self.query_prefetch)


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
            STR_LOOKUP  = ['contains', 'exact', 'startswith', 'endswith', 'regex',
                           'icontains','iexact','istartswith','iendswith','iregex'],
            NUM_LOOKUP  = ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
            DATE_LOOKUP = ['date', 'year', 'iso_year', 'month', 'day', 'week',
                           'week_day', 'quarter', 'time', 'hour', 'minute', 'second'] +
                           ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
            ITER_LOOKUP = ['in'],
            BOOL_LOOKUP = ['exact','iexact'], )
        context['lookup_categories'] = json.dumps(lcats)

        context['avail_fields'] = json.dumps(self.get_avail_fields())

        # Setting default shown columns based on table_class's Meta.base_shown_cols attrib,
        # and "searchcol-" extra_columns (see get_table_kwargs())
        # For Parts and Inventory, set_column_default_show is overwritten
        # such as to hide UDF colums that don't belong / dont have data.
        context['table'].set_column_default_show(self.get_table_data())

        return context

    @staticmethod
    def get_avail_fields():
        # default, this should be overwritten by non-generic search class views
        avail_fields = [dict(value="id", text="Database ID", legal_lookups='BOOL_LOOKUP')]
        return avail_fields

    def get_table_kwargs(self, field_exceptions=[]):
        # Provides additional parameters to table_class upon instantiation.
        # in this case, adds columns from get_avail_fields().
        # Queried fields are prefixed with "searchcol-"
        # such that they will be shown by default by set_column_default_show

        # exclude cols from download
        try: self.exclude_columns = self.request.GET.get('excluded_columns').strip('"').split(',')
        except AttributeError: self.exclude_columns = []

        extra_cols = []
        queried_fields = []

        for card in self.get_search_cards():
            for row in card['rows']:
                for field in row['fields']:
                    if field not in field_exceptions:
                        queried_fields.append(field)
        queried_fields = set(queried_fields)

        for field in self.get_avail_fields():
            if field['value'] is not None \
               and field['value'] not in field_exceptions \
               and field['value'] not in self.table_class.Meta.fields:
                if field['value'] in queried_fields:
                    safename = 'searchcol-{}'.format(field['value'])
                else:
                    if 'extracol' in self.request.GET.getlist('skipcol'): continue
                    #safename = 'extracol-{}'.format(field['value'])
                    safename = '{}'.format(field['value'])

                if 'DATE_LOOKUP' == field['legal_lookups']:
                    col = tables.DateTimeColumn(verbose_name=field['text'], accessor=field['value'])
                elif 'BOOL_LOOKUP' == field['legal_lookups']:
                    col = tables.BooleanColumn(verbose_name=field['text'], accessor=field['value'])
                else:
                    col = tables.Column(verbose_name=field['text'], accessor=field['value'])

                extra_cols.append( (safename,col) )

        return {'extra_columns':extra_cols}


class InventoryTableView(GenericSearchTableView):
    model = Inventory
    table_class = InventoryTable
    query_prefetch = ['fieldvalues', 'fieldvalues__field', 'part', 'location', 'inventory_actions', 'inventory_actions__user', 'inventory_actions__location']
    avail_udf = set()

    @staticmethod
    def get_avail_fields():
        avail_fields = [dict(value="part__name",                     text="Name", legal_lookups='STR_LOOKUP'),
                        dict(value="part__friendly_name",   text="Friendly Name", legal_lookups='STR_LOOKUP'),
                        dict(value="serial_number",         text="Serial Number", legal_lookups='STR_LOOKUP'),
                        dict(value="old_serial_number", text="Old Serial Number", legal_lookups='STR_LOOKUP'),
                        dict(value="location__name",             text="Location", legal_lookups='STR_LOOKUP'),
                        dict(value="build__assembly__name",         text="Build", legal_lookups='STR_LOOKUP'),
                        dict(value="created_at",             text="Date Created", legal_lookups='DATE_LOOKUP'),
                        dict(value="updated_at",            text="Date Modified", legal_lookups='DATE_LOOKUP'),

                        dict(value=None, text="--Part--", disabled=True),
                        dict(value="part__part_number",        text="Part Number", legal_lookups='STR_LOOKUP'),
                        dict(value="part__part_type__name",    text="Part Type",   legal_lookups='STR_LOOKUP'),
                        dict(value="part__revision",         text="Part Revision", legal_lookups='STR_LOOKUP'),
                        dict(value="part__unit_cost",          text="Unit Cost",   legal_lookups='NUM_LOOKUP'),
                        dict(value="part__refurbishment_cost", text="Refurb Cost", legal_lookups='NUM_LOOKUP'),

                        #dict(value=None, text="--Location--", disabled=True),
                        #dict(value="location__name",          text="Name",          legal_lookups='STR_LOOKUP'),
                        #dict(value="location__location_type", text="Location Type", legal_lookups='STR_LOOKUP'),
                        #dict(value="location__root_location", text="Location Root", legal_lookups='STR_LOOKUP'),

                        dict(value=None, text="--User-Defined-Fields--", disabled=True),
                        dict(value="fieldvalues__field__field_name", text="UDF Name",  legal_lookups='STR_LOOKUP'),
                        dict(value="fieldvalues__field_value",       text="UDF Value", legal_lookups='STR_LOOKUP'),

                        dict(value=None, text="--Actions--", disabled=True),
                        dict(value="actions__latest__action_type",    text="Latest Action",           legal_lookups='STR_LOOKUP'),
                        dict(value="actions__latest__user__name",     text="Latest Action: User",     legal_lookups='STR_LOOKUP'),
                        dict(value="actions__latest__created_at",     text="Latest Action: Time",     legal_lookups='DATE_LOOKUP'),
                        dict(value="actions__latest__location__name", text="Latest Action: Location", legal_lookups='STR_LOOKUP'),
                        dict(value="actions__latest__detail",         text="Latest Action: Details",  legal_lookups='STR_LOOKUP'),
                        dict(value="actions__count",                  text="Total Action Count",      legal_lookups='NUM_LOOKUP'),
                        ]
        return avail_fields

    def get_queryset(self):
        qs = super().get_queryset()
        if not 'trash' in self.request.GET.getlist('include'):
            qs = qs.exclude(location__root_type='Trash')
        self.avail_udf.clear()
        [[self.avail_udf.add(fv.field.id) for fv in q.fieldvalues.all()] for q in qs]
        return qs

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs(field_exceptions=self.table_class.Meta.udf_accessors)

        if 'udf' in self.request.GET.getlist('skipcol'):
            return kwargs

        ## UDF ##
        udfname_queries = []
        udfvalue_queries = []
        for card in self.get_search_cards():
            for row in card['rows']:
                if 'fieldvalues__field__field_name' in row['fields']:
                    udfname_queries.append(row['query'])  # capture this row's query
                #elif 'fieldvalues__field_value' in row['fields']:
                #    udfvalue_queries.append(row['query']) # TODO show all UDF that match this ?? How??

        # UDF Cols: these have to be added before the table is made
        # see table_class.set_column_default_show for more
        for udf in Field.objects.all().order_by('id'):

            # don't make a column if no data available for this udf
            if udf.id not in self.avail_udf: continue

            safename =  UDF_Column.prefix+'{:03}'.format(udf.id)
            if any([qry.lower() in udf.field_name.lower() for qry in udfname_queries]):
                safename = 'searchcol-'+safename

            footer_count = 'show-udf-footer-count' in self.request.GET
            bound_coltup = (safename, UDF_Column(udf, accessor='fieldvalues', accessor_type='FieldValue', footer_count=footer_count))
            kwargs['extra_columns'].append( bound_coltup )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class PartTableView(GenericSearchTableView):
    model = Part
    table_class = PartTable
    avail_udf = set()
    query_prefetch = ['user_defined_fields','part_type']

    @staticmethod
    def get_avail_fields():
        avail_fields = [dict(value="name",                        text="Name", legal_lookups='STR_LOOKUP'),
                        dict(value="friendly_name",      text="Friendly Name", legal_lookups='STR_LOOKUP'),
                        dict(value="part_number",          text="Part Number", legal_lookups='STR_LOOKUP'),
                        dict(value="part_type__name",        text="Part Type", legal_lookups='STR_LOOKUP'),
                        dict(value="revision",           text="Part Revision", legal_lookups='STR_LOOKUP'),
                        dict(value="unit_cost",              text="Unit Cost", legal_lookups='NUM_LOOKUP'),
                        dict(value="refurbishment_cost",   text="Refurb Cost", legal_lookups='NUM_LOOKUP'),
                        dict(value="inventory__count", text="Inventory Count", legal_lookups='NUM_LOOKUP'),
                        dict(value="note",                       text="Notes", legal_lookups='STR_LOOKUP'),

                        dict(value=None, text="--User-Defined-Fields--", disabled=True),
                        dict(value="user_defined_fields__field_name", text="UDF Name", legal_lookups='STR_LOOKUP'),]
        return avail_fields

    def get_queryset(self):
        qs = super().get_queryset()
        self.avail_udf.clear()
        [[self.avail_udf.add(udf.id) for udf in q.user_defined_fields.all()] for q in qs]
        return qs

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs(field_exceptions=['user_defined_fields__field_name'])

        if 'udf' in self.request.GET.getlist('skipcol'):
            return kwargs

        udfname_queries = []
        for card in self.get_search_cards():
            for row in card['rows']:
                if 'user_defined_fields__field_name' in row['fields']:
                    udfname_queries.append(row['query'])  # capture this row's query

        # UDF Cols: these have to be added before the table is made
        # see table_class.set_column_default_show for more
        for udf in Field.objects.all().order_by('id'):

            # don't make a column if no data available for this udf
            if udf.id not in self.avail_udf: continue

            safename =  UDF_Column.prefix+'{:03}'.format(udf.id)
            if any([qry.lower() in udf.field_name.lower() for qry in udfname_queries]):
                safename = 'searchcol-'+safename

            footer_count = 'show-udf-footer-count' in self.request.GET
            bound_coltup = (safename, UDF_Column(udf, accessor='user_defined_fields',footer_count=footer_count))
            kwargs['extra_columns'].append( bound_coltup )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class BuildTableView(GenericSearchTableView):
    model = Build
    table_class = BuildTable
    query_prefetch = ['assembly','assembly__assembly_type','location','build_actions']

    @staticmethod
    def get_avail_fields():
        avail_fields = [dict(value="assembly__name",                text="Name", legal_lookups='STR_LOOKUP'),
                        dict(value="build_number",          text="Build Number", legal_lookups='STR_LOOKUP'),
                        dict(value="assembly__assembly_type__name", text="Type", legal_lookups='STR_LOOKUP'),
                        dict(value="location__name",            text="Location", legal_lookups='STR_LOOKUP'),
                        dict(value="assembly__description",  text="Description", legal_lookups='STR_LOOKUP'),
                        dict(value="build_notes",                  text="Notes", legal_lookups='STR_LOOKUP'),
                        dict(value="time_at_sea",            text="Time at Sea", legal_lookups='NUM_LOOKUP'),
                        dict(value="is_deployed",           text="is-deployed?", legal_lookups='BOOL_LOOKUP'),
                        dict(value="flag",                   text="is-flagged?", legal_lookups='BOOL_LOOKUP'),
                        dict(value="created_at",            text="Date Created", legal_lookups='DATE_LOOKUP'),
                        dict(value="updated_at",           text="Date Modified", legal_lookups='DATE_LOOKUP'),

                        #dict(value=None, text="--Location--", disabled=True),
                        #dict(value="location__name",          text="Name", legal_lookups='STR_LOOKUP'),
                        #dict(value="location__location_type", text="Location Type", legal_lookups='STR_LOOKUP'),
                        #dict(value="location__root_type",     text="Root", legal_lookups='STR_LOOKUP'),

                        dict(value=None, text="--Actions--", disabled=True),
                        dict(value="build_actions__latest__action_type",    text="Latest Action",           legal_lookups='STR_LOOKUP'),
                        dict(value="build_actions__latest__user__name",     text="Latest Action: User",     legal_lookups='STR_LOOKUP'),
                        dict(value="build_actions__latest__created_at",     text="Latest Action: Time",     legal_lookups='DATE_LOOKUP'),
                        dict(value="build_actions__latest__location__name", text="Latest Action: Location", legal_lookups='STR_LOOKUP'),
                        dict(value="build_actions__latest__detail",         text="Latest Action: Notes",    legal_lookups='STR_LOOKUP'),
                        dict(value="build_actions__count",                  text="Total Action Count",      legal_lookups='NUM_LOOKUP'),
                        ]

        return avail_fields

    def get_queryset(self):
        qs = super().get_queryset()
        if not 'trash' in self.request.GET.getlist('include'):
            qs = qs.exclude(location__root_type='Trash')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AssemblyTableView(GenericSearchTableView):
    model = Assembly
    table_class = AssemblyTable
    query_prefetch = ['assembly_type']

    @staticmethod
    def get_avail_fields():
        avail_fields = [dict(value="name",                text="Name", legal_lookups='STR_LOOKUP'),
                        dict(value="assembly_number",   text="Number", legal_lookups='STR_LOOKUP'),
                        dict(value="assembly_type__name", text="Type", legal_lookups='STR_LOOKUP'),
                        dict(value="description",  text="Description", legal_lookups='STR_LOOKUP'),
                        ]
        return avail_fields

    def get_queryset(self):
        qs = super().get_queryset()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
