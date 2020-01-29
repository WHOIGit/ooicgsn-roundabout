import json
import socket
import os
import xml.etree.ElementTree as ET

from django.shortcuts import render, get_object_or_404
from django.template.defaultfilters import register
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, QueryDict
from django.db.models import Q
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from itertools import chain

from roundabout.inventory.models import Inventory
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision
from roundabout.userdefinedfields.models import FieldValue
from roundabout.admintools.models import Printer
from roundabout.assemblies.models import AssemblyPart,Assembly
from roundabout.builds.models import Build, BuildAction

class BasicSearch(LoginRequiredMixin, ListView):
    template_name = 'search/search_list.html'
    context_object_name = 'search_items_qs'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super(BasicSearch, self).get_context_data(**kwargs)

        # Check if search query exists, if so add it to context for pagination
        query = self.request.GET.get('q')
        context['query_slug'] = 'q={}'.format(query) if query else ''  #self.request.GET.urlencode()
        context['query'] = query
        context['checked'] = {}
        for gname in ['p','i','n','sn','l','u']:
            context['checked'][gname] = 'checked' if self.request.GET.get(gname)=='✓' else ''
            context['query_slug'] += '&{}=✓'.format(gname) if self.request.GET.get(gname)=='✓' else ''

        context['search_items'] = search_list_item_formatting(context['search_items_qs'])

        limit_paginator(context,25)

        return context

    def get_queryset(self):
        return basic_query(self.request.META['QUERY_STRING'])

def basic_query(qs):
    if not qs: return []
    qs = qs.replace('%E2%9C%93','✓')
    slugs = {pair.split('=',1)[0]:pair.split('=',1)[1] for pair in qs.split('&')}
    slugs = {k:v=='✓' if k!='q' else v for k,v in slugs.items()}

    keywords   = slugs['q']
    parts_bool = slugs['p'] if 'p' in slugs else False
    inv_bool  = slugs['i']  if 'i' in slugs else False
    name_bool = slugs['n']  if 'n' in slugs else False
    sn_bool   = slugs['sn'] if 'sn' in slugs else False
    udf_bool  = slugs['u']  if 'u' in slugs else False
    loc_bool  = slugs['l']  if 'l' in slugs else False

    print(keywords,parts_bool,inv_bool,name_bool,sn_bool)

    qs_inv = Inventory.objects.none()
    qs_prt = Part.objects.none()
    if keywords and any([name_bool,sn_bool,udf_bool]):
        if inv_bool:
            if sn_bool and name_bool: query_inv = Q(serial_number__icontains=keywords)|Q(part__name__icontains=keywords)
            elif sn_bool:             query_inv = Q(serial_number__icontains=keywords)
            elif name_bool:           query_inv = Q(part__name__icontains=keywords)
            else:                     query_inv = Q()
            if udf_bool:
                query_inv = query_inv | Q(fieldvalues__field_value__icontains=keywords)
                query_inv = query_inv | Q(part__user_defined_fields__field_name__icontains=keywords)
            if loc_bool:
                query_inv = query_inv | Q(location__name__icontains=keywords)
            qs_inv = Inventory.objects.filter(query_inv).order_by('serial_number').distinct()

        if parts_bool:
            if sn_bool and name_bool: query_prt = Q(part_number__icontains=keywords)|Q(name__icontains=keywords)
            elif sn_bool:             query_prt = Q(part_number__icontains=keywords)
            elif name_bool:           query_prt = Q(name__icontains=keywords)
            else:                     query_prt = Q()
            if udf_bool:              query_prt = Q(user_defined_fields__field_default_value__icontains=keywords)
                                                  #Q(user_defined_fields__field_name__icontains=keywords) | \
                                                  #Q(user_defined_fields__field_default_value__icontains=keywords)
                #TODO - udf default value for search
            print(Part.objects.filter(query_prt))
            try: qs_prt = Part.objects.filter(query_prt).order_by('part_number').distinct()
            except ValueError: pass

    return list(qs_inv) + list(qs_prt)


def search_list_item_formatting(search_items_qs):
    items = []
    for q in search_items_qs:
        item = dict(id=q.id, type=q.__class__.__name__)
        if isinstance(q, Inventory):
            item['href'] = reverse('inventory:inventory_detail', args=[q.id])
            item['entry'] = '{} - {}'.format(q.serial_number, q.part.name)
            item['subline'] = 'Inventory Location: {}'.format(q.location)
        elif isinstance(q, Part):
            item['href'] = reverse('parts:parts_detail', args=[q.id])
            item['entry'] = '{} - {}'.format(q.part_number, q.name)
            item['subline'] = 'Part Type: {}'.format(q.part_type)
        if isinstance(q, Build):
            item['href'] = reverse('builds:builds_detail', args=[q.id])
            item['entry'] = '{} - {}'.format(q.build_number, q.name)
            item['subline'] = 'Build Location: {}'.format(q.location)
        elif isinstance(q, Assembly):
            item['href'] = reverse('assemblies:assembly_detail', args=[q.id])
            item['entry'] = '{} - {}'.format(q.assembly_number, q.name)
            item['subline'] = 'Assembly Type: {}'.format(q.assembly_type)
        items.append(item)
    return items


def parse_adv_slug(query_slug):
    tups = [pair.split('=', 1) for pair in query_slug.split('&')]
    # eg: ('model', 'inventory') ('m0_f0', 'serial') ('m0_l0', 'icontains') ('m0_q0', '333')
    #                            ('m0_f1', 'serial') ('m0_l1', 'icontains') ('m0_q1', '')
    cards = dict()
    #card = dict(model='',queries={'0':dict(field='',lookup='',query=''),})
    for key, val in tups:
        if key == 'page': continue
        if val == '': val = None
        key = key.split('_')
        if len(key) == 1:
            card_key = key[0]
            try:
                cards[card_key]['model'] = val
            except KeyError:
                cards[card_key] = dict(model=val, queries={})
        elif len(key) == 2:
            card_key, query_key = key
            query_key_type = query_key[0]
            query_key_index = query_key[1:]
            if query_key_type == 'f':
                query_key_type = 'field'
            elif query_key_type == 'l':
                query_key_type = 'lookup'
            elif query_key_type == 'q':
                query_key_type = 'query'
            try:
                cards[card_key]['queries'][query_key_index][query_key_type] = val
            except KeyError:
                cards[card_key]['queries'][query_key_index] = {query_key_type: val}
    for card_key in cards:
        cards[card_key]['queries'] =  {i:flq_dict for i,flq_dict in enumerate(cards[card_key]['queries'].values())}
    return cards

def adv_query(query_slug):
    if not query_slug: return []

    cards = parse_adv_slug(query_slug)

    for card in cards.values():
        model = card['model']
        if model == 'inventory':
            model = Inventory
        elif model == 'part':
            model = Part
        elif model == 'builds':
            model = Build
        elif model == 'assembly':
            model = Assembly
        else:
            continue

        query = None
        for query_dict in card['queries'].values():
            if query_dict['query'] is None: continue
            Q_string = 'Q({field}__{lookup}={query})'.format(**query_dict)
            Q_kwarg = {'{field}__{lookup}'.format(**query_dict): query_dict['query']}
            if query:
                query = query & Q(**Q_kwarg)  # ie Q(<field>__<lookup>=<query>) where eg: field = "part__part_number" and lookup = "icontains"
            else: query = Q(**Q_kwarg)
        if query:
            print(query)
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

    return results if results else []


class AdvSearch(LoginRequiredMixin,ListView):
    template_name = 'search/adv_search.html'
    context_object_name = 'search_items_qs'  # puts stuff returned from get_queryset into context[search_items_qs]
    paginate_by = 20

    def get_queryset(self):
        return adv_query(self.request.META['QUERY_STRING'])

    def get_context_data(self, **kwargs):
        context = super(AdvSearch, self).get_context_data(**kwargs)

        context['query_slug'] = self.request.META['QUERY_STRING']
        if '&page=' in context['query_slug']:
            context['query_slug'] = context['query_slug'].split('&page=')[0]

        if context['query_slug']:
            cards = parse_adv_slug(context['query_slug'])
            context['prev_cards'] = json.dumps(cards)
            print(context['prev_cards'])

        context['search_items'] = search_list_item_formatting(context['search_items_qs'])

        limit_paginator(context,25)

        return context

def limit_paginator(context,max_to_show):
    if context['page_obj'].paginator.num_pages <= max_to_show:
        context['custom_paginator_range'] = context['page_obj'].paginator.page_range
    else:
        currpage = context['page_obj'].number
        maxpage = context['page_obj'].paginator.num_pages
        context['custom_paginator_range'] = range(max(1, currpage-10),
                                                  min(maxpage, currpage+11))
    #print('page', context['page_obj'].number, 'of', context['page_obj'].paginator.num_pages, context['custom_paginator_range'])

import csv
class CsvDownloadSearch(LoginRequiredMixin, View):
    def get(self,request,adv_or_basic,qs):

        if adv_or_basic == 'adv':
            results = adv_query(qs)
        elif adv_or_basic == 'basic':
            results = basic_query(qs)
        else: raise ValueError('must be either "adv" or "basic"')

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
