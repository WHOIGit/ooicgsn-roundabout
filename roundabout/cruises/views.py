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

from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import View, DetailView, ListView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import *
from .forms import VesselForm

# Printer functionality
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
