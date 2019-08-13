import json
import socket
import os
import xml.etree.ElementTree as ET

from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
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

# Mixins
# ------------------------------------------------------------------------------

class InventoryNavTreeMixin(LoginRequiredMixin, object):

    def get_context_data(self, **kwargs):
        context = super(InventoryNavTreeMixin, self).get_context_data(**kwargs)
        context.update({
            'locations': Location.objects.exclude(root_type='Retired')
                        .prefetch_related('builds__assembly__assembly_parts__part__part_type')
                        .prefetch_related('inventory__part__part_type').prefetch_related('builds__inventory').prefetch_related('builds__deployments')
        })
        if 'current_location' in self.kwargs:
            context['current_location'] = self.kwargs['current_location']
        else:
            context['current_location'] = 2

        return context




# Funtion to filter navtree by Part Type
def filter_inventory_navtree(request):
    part_types = request.GET.getlist('part_types[]')
    part_types = list(map(int, part_types))
    locations = Location.objects.prefetch_related('deployments__final_location__mooring_parts__part__part_type') \
                                .prefetch_related('inventory__part__part_type') \
                                .prefetch_related('deployments__inventory')
    return render(request, 'inventory/ajax_inventory_navtree.html', {'locations': locations, 'part_types': part_types})



class Searchbar(InventoryNavTreeMixin, TemplateView):
    # Display a Inventory List page filtered by serial number.
    #model = Inventory
    template_name = 'search/search_list.html'
    #context_object_name = 'search_items'
    #paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super(Searchbar, self).get_context_data(**kwargs)

        # Check if search query exists, if so add it to context for pagination
        keywords = self.request.GET.get('q')
        print('keywords:',keywords)

        if keywords:
            search = 'q=' + keywords
            qs_inv = Inventory.objects.filter( Q(serial_number__icontains=keywords)|Q(part__name__icontains=keywords) )
            qs_part = Part.objects.filter( Q(part_number__icontains=keywords)|Q(name__icontains=keywords) )
        else:
            search = None
            qs_inv = Inventory.objects.none()
            qs_part = Part.objects.none()

        print(qs_inv,qs_part)

        context.update({
            'node_type': 'inventory',
            'navtree_title': 'Inventory',
            'navtree_url': reverse('inventory:ajax_load_inventory_navtree'),
            'search': search,
            'inventory': qs_inv,
            'parts':qs_part,
        })
        return context


class SearchList(InventoryNavTreeMixin, ListView):
    # Display a Inventory List page filtered by serial number.
    #model = Inventory
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

        if model_select == 'inventory':
            context.update({'node_type': 'inventory',
                            'navtree_title': 'Inventory',
                            'navtree_url':reverse('inventory:ajax_load_inventory_navtree')})
        elif model_select == 'parts':
            context.update({'node_type': 'parts',
                            'navtree_title': 'Parts',
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
