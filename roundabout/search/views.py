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


def parse_adv_slug(model, query_slug):
    query_slug = unquote(query_slug)
    tups = [pair.split('=', 1) for pair in query_slug.split('&')]
    # eg: ('model', 'inventory') ('m0_f0', 'serial') ('m0_f0', 'name') ('m0_l0', 'icontains') ('m0_q0', '333')
    #                            ('m0_f1', 'serial')                   ('m0_l1', 'icontains') ('m0_q1', '222')
    cards = dict()
    #card = dict(model='',queries={'0':dict(field=[''],lookup='',query=''),})
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
    if '&' not in query_slug: return model.objects.all()

    cards = parse_adv_slug(model, query_slug)
    if not cards: return model.objects.all()

    for card in cards.values():
        print('NEW CARD:',card)
        query = None
        for query_dict in card.values():
            if query_dict['query'] is None: continue
            multiselect_query = None
            for field in query_dict['fields']:
                Q_string = 'Q({field}__{lookup}={query})'.format(**query_dict, field=field)
                Q_kwarg = {'{field}__{lookup}'.format(field=field, lookup=query_dict['lookup']): query_dict['query']}
                if multiselect_query:
                    multiselect_query = multiselect_query | Q(**Q_kwarg)  # queries from multiselects are is OR'd
                else:
                    multiselect_query = Q(**Q_kwarg)

            if query:
                query = query & multiselect_query  # queries from different rows are AND'd
            else: query = multiselect_query
            # eg: Q(<field>__<lookup>=<query>) where eg: field = "part__part_number" and lookup = "icontains"
        if query:
            print('final card query:',query)
            card['qs'] = model.objects.filter(query).distinct()
        else:
            pass#card['qs'] = model.objects.none()

    results = None
    for card in cards.values():
        if 'qs' not in card.keys(): continue
        if not results:
            results = card['qs']
        else:
            try:
                results = results+card['qs']
            except TypeError as e:
                if str(e).startswith('unsupported operand type(s) for +'):
                    results = list(results)+list(card['qs'])
                else: print(type(e), e)

    return results if results else model.objects.none()

def search_context(context, raw_slug):
    context['query_slug'] = raw_slug
    if '&page=' in context['query_slug']:
        context['query_slug'] = context['query_slug'].split('&page=')[0]

    if context['query_slug']:
        cards = parse_adv_slug(context['model'],context['query_slug'])
        context['prev_cards'] = json.dumps(cards)

    if len(context['search_items_qs']) == 0: context['table'] = None
    return context

import django_tables2 as tables
from django_tables2 import SingleTableView
from .tables import InventoryTable, PartTable, BuildTable, AssemblyTable

class InventoryTableView(LoginRequiredMixin,SingleTableView):
    model = Inventory
    table_class = InventoryTable
    context_object_name = 'search_items_qs'
    template_name = 'search/adv_search.html'

    def get_queryset(self):
        resp = adv_query(self.model, self.request.META['QUERY_STRING'])
        return resp

    def get_context_data(self, **kwargs):
        context = super(InventoryTableView, self).get_context_data(**kwargs)
        context['model']='inventory'
        context['self_url'] = self.request.META['PATH_INFO']
        return search_context(context, self.request.META['QUERY_STRING'])

class PartTableView(LoginRequiredMixin,SingleTableView):
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

class BuildTableView(LoginRequiredMixin,SingleTableView):
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

class AssemblyTableView(LoginRequiredMixin,SingleTableView):
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

import csv
class CsvDownloadSearch(LoginRequiredMixin, View):
    def get(self,request,model,qslug):

        if model == 'inventory':  model=Inventory
        elif model == 'part':     model=Part
        elif model == 'build':    model=Build
        elif model == 'assembly': model=Assembly
        else: return

        results = adv_query(model,qslug)
        response = HttpResponse(content_type='text/csv')
        filename = "search.csv"
        response['Content-Disposition'] = 'attachment; filename='+filename

        header = ['Type','SN','Name','Location','Subtype']
        rows=[]
        for item in results:
            if isinstance(item,Inventory):
                rows.append(['Inventory',item.serial_number,item.part.name,item.location,''])
            elif isinstance(item,Part):
                rows.append(['Part',item.part_number,item.name,'',item.part_type])
            elif isinstance(item,Build):
                rows.append(['Build',item.build_number,item.name,item.location,''])
            elif isinstance(item,Assembly):
                rows.append(['Assembly',item.assembly_number,item.name,'',item.assembly_type])

        writer = csv.writer(response)
        writer.writerow(header)
        writer.writerows(rows)

        return response
