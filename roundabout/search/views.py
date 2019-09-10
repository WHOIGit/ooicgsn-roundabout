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
from roundabout.moorings.models import MooringPart
from roundabout.admintools.models import Printer
from roundabout.assemblies.models import AssemblyPart
from roundabout.builds.models import Build, BuildAction



class SearchList(ListView):
    template_name = 'search/search_list.html'
    context_object_name = 'search_items'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super(SearchList, self).get_context_data(**kwargs)

        # Check if search query exists, if so add it to context for pagination
        keywords = self.request.GET.get('q')
        model_select = self.request.GET.get('m')

        if keywords:
            search = 'q={}&m={}'.format(keywords,model_select)
        else:
            search = None
        context['search'] = search

        count=0
        if model_select == 'inventory':
            if keywords:
                query = Q(serial_number__icontains=keywords)|Q(part__name__icontains=keywords)
                count = Inventory.objects.filter(query).count()
        elif model_select == 'parts':
            if keywords:
                query = Q(part_number__icontains=keywords)|Q(name__icontains=keywords)
                count = Part.objects.filter(query).count()
        context['search_count'] = count

        if model_select == 'inventory':
            context.update({'node_type': 'inventory',
                            'navtree_title': 'Inventory',
                            'navtree_url':reverse('inventory:ajax_load_inventory_navtree')})
        elif model_select == 'parts':
            context.update({'node_type': 'parts',
                            'navtree_title': 'Part Templates',
                            'navtree_url':reverse('parts:ajax_load_parts_navtree')})
        return context

    def get_queryset(self):
        keywords = self.request.GET.get('q')
        model_select = self.request.GET.get('m')

        if model_select == 'inventory':
            qs = Inventory.objects.none()
            if keywords:
                query = Q(serial_number__icontains=keywords)|Q(part__name__icontains=keywords)
                qs = Inventory.objects.filter(query)
            return qs
        elif model_select == 'parts':
            qs = Part.objects.none()
            if keywords:
                query = Q(part_number__icontains=keywords)|Q(name__icontains=keywords)
                qs = Part.objects.filter(query)
            return qs

