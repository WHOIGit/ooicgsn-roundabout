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

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
    FormView,
)

from common.util.mixins import AjaxFormMixin
from roundabout.builds.models import BuildAction
from roundabout.inventory.models import Action
from .forms import LocationForm, LocationDeleteForm
from .models import Location


# AJAX functions for Forms and Navtree
# ------------------------------------------------------------------------------

# Main Navtree function
def load_locations_navtree(request):
    locations = Location.objects.all()
    return render(
        request, "locations/ajax_location_navtree.html", {"locations": locations}
    )


# Location CBV Views for CRUD operations and menu Actions
# ------------------------------------------------------------------------------
# AJAX Views


class LocationsAjaxDetailView(LoginRequiredMixin, DetailView):
    model = Location
    context_object_name = "location"
    template_name = "locations/ajax_location_detail.html"

    def get_context_data(self, **kwargs):
        context = super(LocationsAjaxDetailView, self).get_context_data(**kwargs)

        deployments = self.object.deployed_deployments.order_by(
            "build__assembly", "-deployment_start_date"
        ).select_related("build__assembly")

        context.update({"deployments": deployments})
        return context


class LocationsAjaxUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView
):
    model = Location
    form_class = LocationForm
    context_object_name = "location"
    template_name = "locations/ajax_location_form.html"
    permission_required = "locations.add_location"
    redirect_field_name = "home"

    def form_valid(self, form):
        self.object = form.save()
        # Rebuild the Location MPTT tree
        # Location._tree_manager.rebuild()
        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.id,
                "object_type": self.object.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse("locations:ajax_location_detail", args=(self.object.id,))


class LocationsAjaxCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView
):
    model = Location
    form_class = LocationForm
    context_object_name = "location"
    template_name = "locations/ajax_location_form.html"
    permission_required = "locations.add_location"
    redirect_field_name = "home"

    def form_valid(self, form):
        self.object = form.save()
        # store action history
        self.object.record_action_history(Action.ADD, self.request.user)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.id,
                "object_type": self.object.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse("locations:ajax_location_detail", args=(self.object.id,))


class LocationsAjaxDeleteFormView(
    LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, FormView
):
    form_class = LocationDeleteForm
    context_object_name = "location"
    template_name = "locations/ajax_location_confirm_delete.html"
    permission_required = "locations.add_location"
    redirect_field_name = "home"

    def get_context_data(self, **kwargs):
        context = super(LocationsAjaxDeleteFormView, self).get_context_data(**kwargs)
        location = Location.objects.get(id=self.kwargs["pk"])

        context.update({"location": location})
        return context

    def get_form_kwargs(self):
        kwargs = super(LocationsAjaxDeleteFormView, self).get_form_kwargs()
        if "pk" in self.kwargs:
            kwargs["pk"] = self.kwargs["pk"]
        return kwargs

    def form_valid(self, form):
        new_location = form.cleaned_data["new_location"]
        location_to_delete = Location.objects.get(id=self.kwargs["pk"])

        # Need to check if there's Inventory at this Location. If so, need move them to new Location
        if location_to_delete.inventory.exists():
            for item in location_to_delete.inventory.all():
                item.location = new_location
                item.detail = "Moved to %s from %s" % (new_location, location_to_delete)
                action_record = Action.objects.create(
                    action_type="locationchange",
                    detail=item.detail,
                    location=new_location,
                    user=self.request.user,
                    inventory=item,
                )
                item.save()

        # Need to check if there's Builds at this Location. If so, need move them to new Location
        if location_to_delete.builds.exists():
            for build in location_to_delete.builds.all():
                build.location = new_location
                build.detail = "Moved to %s from %s" % (
                    new_location,
                    location_to_delete,
                )
                build_action_record = BuildAction.objects.create(
                    action_type="locationchange",
                    detail=build.detail,
                    location=new_location,
                    user=self.request.user,
                    build=build,
                )
                build.save()

        if self.request.is_ajax():
            data = {
                "message": "Successfully submitted form data.",
                "parent_id": location_to_delete.parent_id,
                "parent_type": location_to_delete.get_object_type(),
                "object_type": location_to_delete.get_object_type(),
            }
            response = JsonResponse(data)
        else:
            response = HttpResponseRedirect(self.get_success_url())

        # Delete the Location object
        location_to_delete.delete()
        # Rebuild the Location MPTT tree
        Location._tree_manager.rebuild()
        return response

    def get_success_url(self):
        return reverse("locations:locations_home")


# Location Base Views


class LocationsHomeView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "locations/location_list.html"
    context_object_name = "locations"
    permission_required = "locations.add_location"
    redirect_field_name = "home"

    def get_context_data(self, **kwargs):
        context = super(LocationsHomeView, self).get_context_data(**kwargs)
        context.update({"node_type": "locations"})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class LocationsDetailView(LoginRequiredMixin, DetailView):
    model = Location
    context_object_name = "location"
    template_name = "locations/location_detail.html"

    def get_context_data(self, **kwargs):
        context = super(LocationsDetailView, self).get_context_data(**kwargs)
        context.update({"node_type": "locations"})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class LocationsCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Location
    form_class = LocationForm
    context_object_name = "location"
    permission_required = "locations.add_location"
    redirect_field_name = "home"

    def get_context_data(self, **kwargs):
        context = super(LocationsCreateView, self).get_context_data(**kwargs)
        context.update({"locations": Location.objects.all()})
        return context

    def get_success_url(self):
        return reverse("locations:locations_detail", args=(self.object.id,))


class LocationsUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Location
    form_class = LocationForm
    context_object_name = "location"
    permission_required = "locations.add_location"
    redirect_field_name = "home"

    def get_context_data(self, **kwargs):
        context = super(LocationsUpdateView, self).get_context_data(**kwargs)
        context.update({"locations": Location.objects.all()})
        return context

    def get_success_url(self):
        return reverse("locations:locations_detail", args=(self.object.id,))


class LocationsDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Location
    success_url = reverse_lazy("locations:locations_home")
    permission_required = "locations.add_location"
    redirect_field_name = "home"
