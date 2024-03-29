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
from datetime import datetime

from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import View, DetailView, ListView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import *
from .forms import VesselForm, CruiseForm
from roundabout.inventory.models import Action
from common.util.mixins import AjaxFormMixin

# Private functions for use in other Views
# ------------------------------------------------------------------------------
def _get_inventory_only_deployments(cruise):
    inventory_deployments = cruise.actions.filter(deployment_type='inventory_deployment').filter(action_type=Action.DEPLOYMENTTOFIELD)
    inventory_deployed = [action.inventory for action in inventory_deployments]

    inventory_recoveries = cruise.actions.filter(deployment_type='inventory_deployment').filter(action_type=Action.DEPLOYMENTRECOVER)
    inventory_recovered = [action.inventory for action in inventory_recoveries]
    return {'inventory_deployed': inventory_deployed, 'inventory_recovered': inventory_recovered}


# AJAX functions for Forms and Navtree
# ------------------------------------------------------------------------------

# Main Navtree function
def load_cruises_navtree(request):
    cruises = Cruise.objects.all()
    return render(request, 'cruises/ajax_cruise_navtree.html', {'cruises': cruises})


# Cruise Base Views
# Landing page template view to contain AJAX templates and handle direct links
class CruiseHomeView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'cruises/cruise_home.html'
    context_object_name = 'cruises'
    permission_required = 'cruises.view_cruise'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(CruiseHomeView, self).get_context_data(**kwargs)
        cruise_pk = kwargs.pop('pk', '')
        cruise_year = kwargs.pop('cruise_year', datetime.now().year)

        cruise = None
        if cruise_pk:
            try:
                cruise = Cruise.objects.get(id=cruise_pk)
            except Cruise.DoesNotExist:
                pass

        inventory_deployed = None
        inventory_recovered = None
        if cruise:
            inventory_deployments = _get_inventory_only_deployments(cruise)
            inventory_deployed = inventory_deployments['inventory_deployed']
            inventory_recovered = inventory_deployments['inventory_recovered']

        cruises = None
        if cruise_year:
            cruises = Cruise.objects.filter(cruise_start_date__year=cruise_year)

        context.update({
            'cruise': cruise,
            'cruises': cruises,
            'node_type': 'cruises',
            'cruise_year': cruise_year,
            'inventory_deployed': inventory_deployed,
            'inventory_recovered': inventory_recovered,
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# Cruise CBV Views for CRUD operations and menu Actions
# ------------------------------------------------------------------------------
# AJAX Views

class CruiseAjaxDetailView(LoginRequiredMixin, DetailView):
    model = Cruise
    context_object_name = 'cruise'
    template_name='cruises/ajax_cruise_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CruiseAjaxDetailView, self).get_context_data(**kwargs)
        inventory_deployments = _get_inventory_only_deployments(self.object)
        inventory_deployed = inventory_deployments['inventory_deployed']
        inventory_recovered = inventory_deployments['inventory_recovered']

        context.update({
            'inventory_deployed': inventory_deployed,
            'inventory_recovered': inventory_recovered,
        })
        return context


class CruiseAjaxCruisesByYearView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'cruises/ajax_cruise_by_year.html'
    context_object_name = 'cruises'
    permission_required = 'cruises.view_cruise'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(CruiseAjaxCruisesByYearView, self).get_context_data(**kwargs)
        cruise_year = self.kwargs['cruise_year']
        cruises = Cruise.objects.filter(cruise_start_date__year=cruise_year)
        context.update({
            'cruises': cruises,
            'cruise_year': cruise_year,
        })
        return context


# Create view for Cruises
class CruiseAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Cruise
    form_class = CruiseForm
    context_object_name = 'cruise'
    template_name='cruises/ajax_cruise_form.html'

    def form_valid(self, form):
        self.object = form.save()
        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse('cruises:ajax_cruises_detail', args=(self.object.id,))


# Update view for builds
class CruiseAjaxUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = Cruise
    form_class = CruiseForm
    context_object_name = 'cruise'
    template_name='cruises/ajax_cruise_form.html'

    def form_valid(self, form):
        self.object = form.save()
        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse('cruises:ajax_cruises_detail', args=(self.object.id,))


class CruiseAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Cruise
    template_name = 'cruises/ajax_cruise_confirm_delete.html'
    permission_required = 'cruises.delete_cruise'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.cruise_start_date.year,
            'parent_type': 'year_group',
            'object_type': self.object.get_object_type(),
        }
        self.object.delete()

        return JsonResponse(data)


# Vessel CBV views
# ----------------------

class VesselListView(LoginRequiredMixin, ListView):
    model = Vessel
    template_name = 'cruises/vessel_list.html'
    context_object_name = 'vessels'


class VesselCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Vessel
    form_class = VesselForm
    context_object_name = 'vessel'
    permission_required = 'cruises.add_vessel'
    redirect_field_name = 'home'

    def get_success_url(self):
        return reverse('cruises:vessels_home', )

class VesselUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Vessel
    form_class = VesselForm
    context_object_name = 'vessel'
    permission_required = 'cruises.change_vessel'
    redirect_field_name = 'home'

    def get_success_url(self):
        return reverse('cruises:vessels_home', )


class VesselDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Vessel
    success_url = reverse_lazy('cruises:vessels_home')
    permission_required = 'cruises.delete_vessel'
    redirect_field_name = 'home'
