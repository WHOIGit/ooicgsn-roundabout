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
from django.conf import settings
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


from .requests import _sync_main
from .models import *
from .forms import *

# Views to handle syncing requests
# --------------------------------
class FieldInstanceSyncToHomeView(View):

    def get(self, request, *args, **kwargs):
        # Get the FieldInstance object that is current
        field_instance = FieldInstance.objects.filter(is_this_instance=True).first()
        if not field_instance:
            return HttpResponse('ERROR. This is not a Field Instance of RDB.')
        user_list = field_instance.users

        sync_code = _sync_main(request, field_instance)
        print(sync_code)

        if sync_code == 200:
            return HttpResponse("Code 200")
        else:
            return HttpResponse("API error")


# Basic CBVs to handle CRUD operations
# -----------------------------------

class FieldInstanceListView(LoginRequiredMixin, ListView):
    model = FieldInstance
    template_name = 'field_instances/field_instance_list.html'
    context_object_name = 'field_instances'


class FieldInstanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = FieldInstance
    form_class = FieldInstanceForm
    template_name = 'field_instances/field_instance_form.html'
    context_object_name = 'field_instance'
    permission_required = 'field_instances.add_fieldinstance'
    redirect_field_name = 'home'

    def get_success_url(self):
        return reverse('field_instances:field_instances_home', )


class FieldInstanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FieldInstance
    form_class = FieldInstanceForm
    template_name = 'field_instances/field_instance_form.html'
    context_object_name = 'field_instance'
    permission_required = 'field_instances.add_fieldinstance'
    redirect_field_name = 'home'

    def get_success_url(self):
        return reverse('field_instances:field_instances_home', )


class FieldInstanceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = FieldInstance
    success_url = reverse_lazy('field_instances:field_instances_home')
    permission_required = 'field_instances.delete_fieldinstance'
    redirect_field_name = 'home'
