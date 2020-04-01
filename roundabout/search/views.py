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

import operator  # for direct access to | ~ & operators used by Q objects
import json
import socket
import os
import xml.etree.ElementTree as ET
from urllib.parse import unquote

from django.shortcuts import render, get_object_or_404
from django.template.defaultfilters import register
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, QueryDict
from django.db.models import Q
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from itertools import chain
from django.shortcuts import redirect

from roundabout.inventory.models import Inventory
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision
from roundabout.userdefinedfields.models import FieldValue
from roundabout.admintools.models import Printer
from roundabout.assemblies.models import AssemblyPart,Assembly
from roundabout.builds.models import Build, BuildAction
from roundabout.userdefinedfields.models import Field


def searchbar_redirect(request):
    print('SEARCHBAR: ',request.GET)
    model = request.GET['model']
    url = 'search:'+model

    query = request.GET['query']
    if query:
        if model=='inventory':      get = '?m0_f0=serial_number&m0_f0=part__name&m0_l0=icontains&m0_q0={query}'
        elif model=='part':         get = '?m0_f0=part_number&m0_f0=name&m0_l0=icontains&m0_q0={query}'
        elif model == 'build':      get = '?m0_f0=assembly__name&m0_f0=assembly__assembly_type__name&m0_f0=location__name&m0_l0=icontains&m0_q0={query}'
        elif model == 'assembly':   get = '?m0_f0=assembly_number&m0_f0=name&m0_f0=assembly_type__name&m0_f0=description&m0_l0=icontains&m0_q0={query}'
        get = get.format(query=query)
        resp = redirect(url)
        resp['Location'] += get
    return resp


def parse_adv_slug(query_slug):
    query_slug = unquote(query_slug)
    tups = [pair.split('=', 1) for pair in query_slug.split('&')]
    # eg: ('model', 'inventory') ('m0_f0', 'serial') ('m0_f0', 'name') ('m0_l0', 'icontains') ('m0_q0', '333')
    #                            ('m0_f1', 'serial')                   ('m0_l1', 'icontains') ('m0_q1', '222')
    cards = dict()
    #card = dict(rows=[dict(field=[''], lookup='', query='', nega=False)])
    for key, val in tups:
        if key == 'page': continue
        if val == '': val = None
        key = key.split('_')
        if len(key) == 2:
            card_key, query_key = key
            query_key_type = query_key[0]
            query_key_index = query_key[1:]

            if query_key_type == 'f':
                query_key_type = 'fields'
                val = [val]
            elif query_key_type == 'l':
                query_key_type = 'lookup'
            elif query_key_type == 'q':
                query_key_type = 'query'
                val = val.replace('+', ' ')
                print('query:',val)

            try:
                if query_key_type == 'fields':
                    try: cards[card_key][query_key_index][query_key_type].extend(val)
                    except AttributeError: cards[card_key][query_key_index][query_key_type] = val
                else:
                    cards[card_key][query_key_index][query_key_type] = val
            except KeyError:
                try: cards[card_key][query_key_index] = {query_key_type: val}
                except KeyError:
                    cards[card_key] = {query_key_index:{query_key_type: val}}

    for card_key in cards: # cleanup of card numbers
        cards[card_key] =  {i:flq_dict for i,flq_dict in enumerate(cards[card_key].values())}
    return cards


def adv_query(model, query_slug):

    cards = parse_adv_slug(query_slug)

    final_Qs = []
    for card in cards.values():
        print('CARD:',card)
        card_Qs = []
        for row in card.values():
            if row['query'] is None: continue  # skip this row
            Q_kwargs = []
            for field in row['fields']:
                # TODO: field x lookup VALIDATION HERE
                # eg: Q(<field>__<lookup>=<query>) where eg: field = "part__part_number" and lookup = "icontains"
                #Q_string = 'Q({field}__{lookup}={query})'.format(**row, field=field)
                Q_kwarg = {'{field}__{lookup}'.format(field=field, lookup=row['lookup']): row['query']}
                Q_kwargs.append(Q_kwarg)

            if len(Q_kwargs) > 1:
                row_Q = operator.or_(*[Q(**Q_kwarg) for Q_kwarg in Q_kwargs])
            elif Q_kwargs:
                row_Q = Q(**Q_kwargs[0])
            else:
                row_Q = None
            #if row['nega'] and row_Q:
            #    row_Q = operator.inv(row_Q)
            if row_Q:
                card_Qs.append(row_Q)
            # ROW DONE
        if len(card_Qs)>1:
            card_Q = operator.and_(*card_Qs)
        elif card_Qs:
            card_Q = card_Qs[0]
        else:
            card_Q = None
        if card_Q:
            final_Qs.append(card_Q)
        # CARD DONE

    if len(final_Qs)>1:
        final_Q = operator.or_(*final_Qs)
    elif final_Qs:
        final_Q = final_Qs[0]
    else:
        final_Q = None

    if final_Q:
        return model.objects.filter(final_Q).distinct()
    else:
        return model.objects.all().exclude(location__root_type='Trash')


def search_context(context, raw_slug):
    context['query_slug'] = raw_slug
    if '&page=' in context['query_slug']:
        context['query_slug'] = context['query_slug'].split('&page=')[0]

    if context['query_slug']:
        cards = parse_adv_slug(context['query_slug'])
        context['prev_cards'] = json.dumps(cards)

    #if len(context['query_objs']) == 0: context['table'] = None
    return context

import django_tables2 as tables
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

from .tables import InventoryTable, PartTable, BuildTable, AssemblyTable, UDF_FIELDS, UDF_Column

class InventoryTableView(LoginRequiredMixin,ExportMixin,SingleTableView):
    model = Inventory
    table_class = InventoryTable
    context_object_name = 'query_objs'
    template_name = 'search/adv_search.html'
    exclude_columns = []

    def get_table_kwargs(self):
        extra_cols = []
        for udf in UDF_FIELDS:
            safename =  UDF_Column.prefix+'{:03}'.format(udf.id) #+'--'+''.join([ c if c.isalnum() or c=='-' else '_' for c in udf.field_name.lower().replace(' ','-').replace('id','xx') ])
            #print('{} {:>3}'.format(udf.id, safename))
            extra_cols.append( (safename, UDF_Column(udf)) )
        #exclude cols from download
        #try: self.exclude_columns = self.request.GET.get('excluded_columns').split(',')
        #except AttributeError: self.exclude_columns = []
        return {'extra_columns':extra_cols}

    def get_queryset(self):
        if self.request.META['QUERY_STRING'].startswith('m0_'):
            resp = adv_query(self.model, self.request.META['QUERY_STRING'])
        else:
            qs = self.model.objects.all().exclude(location__root_type='Trash').order_by('id')
            resp = qs
        return resp

    def get_context_data(self, **kwargs):
        context = super(InventoryTableView, self).get_context_data(**kwargs)
        context['model']='inventory'
        context['self_url'] = self.request.META['PATH_INFO']

        #cols = {name:col.column for name,col in context['table'].columns.columns.items()}
        #col_names = [name for name,col in cols.items()]

        # setting default shown columns, only columns who which have any data* in them will show
        # * well actually it looks at the Part of the inventory and keeps all UDF's that appear there for the whole table.
        context['table'].set_column_default_show(self.get_table_data())

        print('SHOWME:',context['table'].column_default_show)

        context.update(search_context(context, self.request.META['QUERY_STRING']))
        print(' '*10+'CONTEXT END')
        return context

class PartTableView(LoginRequiredMixin,ExportMixin,SingleTableView):
    model = Part
    table_class = PartTable
    context_object_name = 'search_items_qs'
    template_name = 'search/adv_search.html'

    def get_queryset(self):
        resp = adv_query(self.model, self.request.META['QUERY_STRING'])
        return resp

    def get_context_data(self, **kwargs):
        context = super(PartTableView, self).get_context_data(**kwargs)
        context['model']='part'
        context['self_url'] = self.request.META['PATH_INFO']
        return search_context(context, self.request.META['QUERY_STRING'])

class BuildTableView(LoginRequiredMixin,ExportMixin,SingleTableView):
    model = Build
    table_class = BuildTable
    context_object_name = 'search_items_qs'
    template_name = 'search/adv_search.html'

    def get_queryset(self):
        resp = adv_query(self.model, self.request.META['QUERY_STRING'])
        return resp

    def get_context_data(self, **kwargs):
        context = super(BuildTableView, self).get_context_data(**kwargs)
        context['model']='build'
        context['self_url'] = self.request.META['PATH_INFO']
        return search_context(context, self.request.META['QUERY_STRING'])

class AssemblyTableView(LoginRequiredMixin,ExportMixin,SingleTableView):
    model = Assembly
    table_class = AssemblyTable
    context_object_name = 'search_items_qs'
    template_name = 'search/adv_search.html'

    def get_queryset(self):
        resp = adv_query(self.model, self.request.META['QUERY_STRING'])
        return resp

    def get_context_data(self, **kwargs):
        context = super(AssemblyTableView, self).get_context_data(**kwargs)
        context['model']='assembly'
        context['self_url'] = self.request.META['PATH_INFO']
        return search_context(context, self.request.META['QUERY_STRING'])

