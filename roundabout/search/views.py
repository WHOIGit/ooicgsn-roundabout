import json
import socket
import os
import xml.etree.ElementTree as ET

from django.shortcuts import render, get_object_or_404
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
from roundabout.moorings.models import MooringPart
from roundabout.admintools.models import Printer
from roundabout.assemblies.models import AssemblyPart
from roundabout.builds.models import Build, BuildAction

class BasicSearch(LoginRequiredMixin, ListView):
    template_name = 'search/search_list.html'
    context_object_name = 'search_items_qs'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super(BasicSearch, self).get_context_data(**kwargs)

        # Check if search query exists, if so add it to context for pagination
        query = self.request.GET.get('q')
        context['checked'] = {}
        for gname in ['p','i','n','sn','l','u']:
            context['checked'][gname] = 'checked' if self.request.GET.get(gname)=='✓' else ''
        print(context['checked'])

        if query:
            query_str = 'q={}'.format(query)
        else:
            query_str = None
        context['query'] = query
        context['query_slug'] = query_str

        context['search_items'] = []
        for q in context['search_items_qs']:
            item = {}
            item['id'] = q.id
            item['type'] = q.__class__.__name__
            if isinstance(q,Inventory):
                item['href'] = reverse('inventory:inventory_detail',args=[q.id])
                item['entry'] = '{} - {}'.format(q.serial_number,q.part.name)
                item['subline'] = 'Inventory Location: {}'.format(q.location)
            elif isinstance(q,Part):
                item['href'] = reverse('parts:parts_detail',args=[q.id])
                item['entry'] = '{} - {}'.format(q.part_number,q.name)
                item['subline'] = 'Part Type: {}'.format(q.part_type)

            context['search_items'].append(item)
        return context

    def get_queryset(self):
        keywords = self.request.GET.get('q')
        parts_bool = self.request.GET.get('p') == '✓'
        inventory_bool = self.request.GET.get('i') == '✓'
        name_bool = self.request.GET.get('n') == '✓'
        sn_bool = self.request.GET.get('sn') == '✓'
        udf_bool= self.request.GET.get('u') == '✓'
        loc_bool= self.request.GET.get('l') == '✓'

        qs_inv = Inventory.objects.none()
        qs_prt = Part.objects.none()
        if keywords and any([name_bool,sn_bool,udf_bool]):
            if inventory_bool:
                if sn_bool and name_bool: query_inv = Q(serial_number__icontains=keywords)|Q(part__name__icontains=keywords)
                elif sn_bool:             query_inv = Q(serial_number__icontains=keywords)
                elif name_bool:           query_inv = Q(part__name__icontains=keywords)
                if udf_bool:
                    query_inv = query_inv | Q(fieldvalues__field_value__icontains=keywords)
                    query_inv = query_inv | Q(part__user_defined_fields__field_name__icontains=keywords)
                if loc_bool:
                    query_inv = query_inv | Q(location__name__icontains=keywords)
                qs_inv = Inventory.objects.filter(query_inv).order_by('serial_number')

            if parts_bool:
                if sn_bool and name_bool: query_prt = Q(part_number__icontains=keywords)|Q(name__icontains=keywords)
                elif sn_bool:             query_prt = Q(part_number__icontains=keywords)
                elif name_bool:           query_prt = Q(name__icontains=keywords)
                if udf_bool:              query_prt = query_prt | Q(user_defined_fields__field_name__icontains=keywords)

                try: qs_prt = Part.objects.filter(query_prt).order_by('part_number')
                except ValueError: pass

        return list(qs_inv) + list(qs_prt)
