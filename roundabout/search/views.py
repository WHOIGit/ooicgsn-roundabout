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

from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

from roundabout.inventory.models import Inventory
from roundabout.parts.models import Part
from roundabout.assemblies.models import Assembly
from roundabout.builds.models import Build

from .tables import InventoryTable, PartTable, BuildTable, AssemblyTable, UDF_FIELDS, UDF_Column


def searchbar_redirect(request):
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

        # Setting default shown columns, only columns who which have any data* in them will show
        # * well actually it looks at the Part of the inventory and keeps all UDF's that appear there for the whole table.
        context['table'].set_column_default_show(self.get_table_data())

        return context


class InventoryTableView(GenericSearchTableView):
    model = Inventory
    table_class = InventoryTable

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
        qs = super().get_queryset()
        qs = qs.exclude(location__root_type='Trash')
        fetch_me = ['fieldvalues','fieldvalues__field','part','location','revision']
        qs = qs.prefetch_related(*fetch_me)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #TODO pass on fields to include with <options>
        return context


class PartTableView(GenericSearchTableView):
    model = Part
    table_class = PartTable

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #TODO pass on fields to include with <options>
        return context


class BuildTableView(GenericSearchTableView):
    model = Build
    table_class = BuildTable

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #TODO pass on fields to include with <options>
        return context


class AssemblyTableView(GenericSearchTableView):
    model = Assembly
    table_class = AssemblyTable

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #TODO pass on fields to include with <options>
        return context

