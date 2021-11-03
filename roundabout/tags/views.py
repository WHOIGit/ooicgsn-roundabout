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

import re
import json

from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, FormView, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError

from .models import Tag
from .forms import TagForm
from roundabout.inventory.models import AssemblyPart

from common.util.mixins import AjaxFormMixin


class TagAjaxCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = Tag
    context_object_name = 'tag'
    template_name= 'tags/ajax_tag_form.html'
    form_class = TagForm
    permission_required = 'assemblies.change_assembly'

    def get(self, request, *args, **kwargs):
        self.object = None
        assemblypart_id = request.GET.get('a')
        assembly_part = AssemblyPart.objects.get(id=assemblypart_id) if assemblypart_id else None
        self.initial.update(assembly_part=assembly_part, text='{}')
        form = self.get_form()
        return self.render_to_response(self.get_context_data(assembly_part=assembly_part, form=form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()

        if self.request.is_ajax():
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(data, status=400)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('assemblies:ajax_assemblyparts_detail', args=(self.object.assembly_part.id,))


class TagAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tag
    context_object_name = 'tag'
    permission_required = "assemblies.change_assembly"

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def get_success_url(self):
        #return reverse('assemblies:ajax_assemblyparts_detail', args=(self.object.assembly_part.id,))
        target = f'/assemblies/assemblypart/{self.object.assembly_part_id}'
        url = self.request.build_absolute_uri().replace(self.request.get_full_path(), target)
        return url

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponseRedirect( self.get_success_url() )
