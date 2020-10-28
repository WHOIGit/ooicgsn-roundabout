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
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .forms import UserDefinedFieldForm
from .models import Field, FieldValue

# UDF functionality

class UserDefinedFieldListView(LoginRequiredMixin, ListView):
    model = Field
    template_name = 'field_list.html'
    context_object_name = 'fields'


class UserDefinedFieldCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Field
    form_class = UserDefinedFieldForm
    context_object_name = 'field'
    permission_required = 'userdefinedfields.add_field'
    redirect_field_name = 'home'

    def form_valid(self, form):
        self.object = form.save()
        # If field is a global for Part Types, add field to all Parts
        if self.object.global_for_part_types:
            part_types = self.object.global_for_part_types

            for part_type in part_types.all():
                parts = part_type.parts

                for part in parts.all():
                    part.user_defined_fields.add(self.object)

                    # If custom field has a default value, add it to any existing Inventory items
                    if self.object.field_default_value:
                        for item in part.inventory.all():
                            # create new value object
                            fieldvalue = FieldValue.objects.create(field=self.object, field_value=self.object.field_default_value,
                                                                   inventory=item, is_current=True, is_default_value=True)


        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('userdefinedfields:fields_home', )


class UserDefinedFieldUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Field
    form_class = UserDefinedFieldForm
    context_object_name = 'field'
    permission_required = 'userdefinedfields.add_field'
    redirect_field_name = 'home'

    def form_valid(self, form):
        self.object = form.save()
        # If field is a global for Part Types, add field to all Parts
        if self.object.global_for_part_types:
            part_types = self.object.global_for_part_types

            for part_type in part_types.all():
                parts = part_type.parts

                for part in parts.all():
                    part.user_defined_fields.add(self.object)

                    # If custom field has a default value, add it to any existing Inventory items that has no existing value
                    if self.object.field_default_value:
                        for item in part.inventory.all():
                            try:
                                currentvalue = item.fieldvalues.filter(field=self.object).latest()
                            except FieldValue.DoesNotExist:
                                currentvalue = None

                            if not currentvalue:
                                # create new value object if no current value
                                fieldvalue = FieldValue.objects.create(field=self.object, field_value=self.object.field_default_value,
                                                                   inventory=item, is_current=True, is_default_value=True)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('userdefinedfields:fields_home', )


class UserDefinedFieldDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Field
    success_url = reverse_lazy('userdefinedfields:fields_home')
    permission_required = 'userdefinedfields.delete_field'
    redirect_field_name = 'home'
