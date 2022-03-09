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
from django.views.generic import (
    View,
    DetailView,
    ListView,
    UpdateView,
    CreateView,
    DeleteView,
    TemplateView,
    FormView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django_tables2 import SingleTableMixin, SingleTableView
from django_tables2.export.views import ExportMixin

from .tables import *
from .models import *
from .forms import (
    VesselForm,
    CruiseForm,
    VesselHyperlinkFormset,
    CruiseHyperlinkFormset,
    CruiseEventForm
)
from roundabout.inventory.models import Action
from roundabout.inventory.utils import _create_action_history, logged_user_review_items
from common.util.mixins import AjaxFormMixin
from roundabout.calibrations.utils import handle_reviewers, user_ccc_reviews

# Private functions for use in other Views
# ------------------------------------------------------------------------------
def _get_inventory_only_deployments(cruise):
    inventory_deployments = cruise.actions.filter(
        deployment_type="inventory_deployment"
    ).filter(action_type=Action.DEPLOYMENTTOFIELD)
    inventory_deployed = [action.inventory for action in inventory_deployments]

    inventory_recoveries = cruise.actions.filter(
        deployment_type="inventory_deployment"
    ).filter(action_type=Action.DEPLOYMENTRECOVER)
    inventory_recovered = [action.inventory for action in inventory_recoveries]
    return {
        "inventory_deployed": inventory_deployed,
        "inventory_recovered": inventory_recovered,
    }


# AJAX functions for Forms and Navtree
# ------------------------------------------------------------------------------

# Main Navtree function
def load_cruises_navtree(request):
    cruises = Cruise.objects.all()
    reviewer_list = logged_user_review_items(request.user, "cruise")
    return render(request, "cruises/ajax_cruise_navtree.html", {"cruises": cruises, 'reviewer_list': reviewer_list})


# Cruise Base Views
# Landing page template view to contain AJAX templates and handle direct links

class CruiseHomeView(LoginRequiredMixin, SingleTableMixin, ExportMixin, TemplateView):
    template_name = 'cruises/cruise_home.html'
    context_object_name = 'cruises'
    redirect_field_name = 'home'
    model = Cruise
    table_class = CruiseActionTable
    export_name = 'cruise_history__{cruise}'

    def get_context_data(self, **kwargs):
        context = super(CruiseHomeView, self).get_context_data(**kwargs)
        cruise_pk = kwargs.pop("pk", "")
        cruise_year = kwargs.pop("cruise_year", datetime.now().year)

        cruise = None
        if cruise_pk:
            try:
                cruise = Cruise.objects.get(id=cruise_pk)
                history_table_qs = Action.objects.filter(
                    cruise__pk__exact=cruise_pk, object_type__exact=Action.CRUISE
                )
                context["history_table"] = CruiseActionTable(history_table_qs)
            except Cruise.DoesNotExist:
                pass

        inventory_deployed = None
        inventory_recovered = None
        if cruise:
            inventory_deployments = _get_inventory_only_deployments(cruise)
            inventory_deployed = inventory_deployments["inventory_deployed"]
            inventory_recovered = inventory_deployments["inventory_recovered"]

        cruises = None
        if cruise_year:
            cruises = Cruise.objects.filter(cruise_start_date__year=cruise_year)

        context.update(
            {
                "cruise": cruise,
                "cruises": cruises,
                "node_type": "cruises",
                "cruise_year": cruise_year,
                "inventory_deployed": inventory_deployed,
                "inventory_recovered": inventory_recovered,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_table_data(self):
        cruise_pk = self.kwargs.get('pk')
        qs = Action.objects.filter(cruise__pk__exact=cruise_pk, object_type__exact=Action.CRUISE)
        return qs

    def get_export_filename(self, export_format):
        cruise = Cruise.objects.get(pk=self.kwargs['pk'])
        cruise_name = str(cruise).replace('/','').replace(' ','_')
        export_name = self.export_name.format(cruise=cruise_name)
        return "{}.{}".format(export_name, export_format)

# Cruise CBV Views for CRUD operations and menu Actions
# ------------------------------------------------------------------------------
# AJAX Views


class CruiseAjaxDetailView(LoginRequiredMixin, DetailView, SingleTableMixin):
    model = Cruise
    context_object_name = "cruise"
    template_name = "cruises/ajax_cruise_detail.html"
    table_class = CruiseActionTable

    def get_table_data(self):
        cruise_pk = self.kwargs.get("pk")
        qs = Action.objects.filter(
            cruise__pk__exact=cruise_pk, object_type__exact=Action.CRUISE
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super(CruiseAjaxDetailView, self).get_context_data(**kwargs)
        inventory_deployments = _get_inventory_only_deployments(self.object)
        inventory_deployed = inventory_deployments["inventory_deployed"]
        inventory_recovered = inventory_deployments["inventory_recovered"]

        context.update(
            {
                "inventory_deployed": inventory_deployed,
                "inventory_recovered": inventory_recovered,
            }
        )
        context["history_table"] = self.get_table(**self.get_table_kwargs())
        return context


class CruiseAjaxCruisesByYearView(LoginRequiredMixin, TemplateView):
    template_name = "cruises/ajax_cruise_by_year.html"
    context_object_name = "cruises"
    redirect_field_name = "home"

    def get_context_data(self, **kwargs):
        context = super(CruiseAjaxCruisesByYearView, self).get_context_data(**kwargs)
        cruise_year = self.kwargs["cruise_year"]
        cruises = Cruise.objects.filter(cruise_start_date__year=cruise_year)
        context.update(
            {
                "cruises": cruises,
                "cruise_year": cruise_year,
            }
        )
        return context


# Create view for Cruises
class CruiseAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Cruise
    form_class = CruiseForm
    context_object_name = "cruise"
    template_name = "cruises/ajax_cruise_form.html"

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = CruiseHyperlinkFormset(instance=self.object)
        return self.render_to_response(
            self.get_context_data(form=form, link_formset=link_formset)
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = CruiseHyperlinkFormset(self.request.POST, instance=self.object)

        if form.is_valid() and link_formset.is_valid():
            return self.form_valid(form, link_formset)
        return self.form_invalid(form, link_formset)

    def form_valid(self, form, formset):
        self.object = form.save()

        data = dict(updated_values=dict())
        for field in form.fields:
            val = getattr(self.object, field, None)
            if val:
                data["updated_values"][field] = {"from": None, "to": str(val)}
        _create_action_history(self.object, Action.ADD, self.request.user, data=data)

        for link_form in formset:
            link = link_form.save(commit=False)
            if link.text and link.url:
                link.parent = self.object
                link.save()

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.id,
                "object_type": self.object.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, formset):
        if self.request.is_ajax():
            if not form.is_valid():
                # show form errors before formset errors
                return JsonResponse(form.errors, status=400)
            else:
                # only show formset errors if there are no form errors
                # because it is unclear how to combine form and formset errors in a way that doesnt break project.js:handleFormError()
                return JsonResponse(formset.errors, status=400, safe=False)
        else:
            return self.render_to_response(
                self.get_context_data(form=form, link_formset=formset)
            )

    def get_success_url(self):
        return reverse("cruises:ajax_cruises_detail", args=(self.object.id,))


# Update view for builds
class CruiseAjaxUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = Cruise
    form_class = CruiseForm
    context_object_name = "cruise"
    template_name = "cruises/ajax_cruise_form.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = CruiseHyperlinkFormset(instance=self.object)
        return self.render_to_response(
            self.get_context_data(form=form, link_formset=link_formset)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = CruiseHyperlinkFormset(self.request.POST, instance=self.object)

        if form.is_valid() and link_formset.is_valid():
            return self.form_valid(form, link_formset)
        return self.form_invalid(form, link_formset)

    def form_valid(self, form, formset):
        orig_obj = Cruise.objects.get(pk=self.object.pk)
        new_obj = form.save(commit=False)

        data = dict(updated_values=dict())
        for field in form.fields:
            orig_val = getattr(orig_obj, field, None)
            new_val = getattr(new_obj, field, None)
            if orig_val != new_val:
                data["updated_values"][field] = {
                    "from": str(orig_val),
                    "to": str(new_val),
                }
        self.object = form.save(commit=True)
        cruise_event_form = CruiseEventForm(instance=self.object.cruise_event)
        handle_reviewers(cruise_event_form.instance.user_draft, cruise_event_form.instance.user_approver, form.cleaned_data['user_draft'])
        _create_action_history(self.object, Action.UPDATE, self.request.user, data=data)
        _create_action_history(self.object.cruise_event, Action.UPDATE, self.request.user, data=data)

        for link_form in formset:
            link = link_form.save(commit=False)
            if link.text and link.url:
                if link_form["DELETE"].data:
                    link.delete()
                else:
                    link.parent = self.object
                    link.save()

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.id,
                "object_type": self.object.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, formset):
        if self.request.is_ajax():
            if not form.is_valid():
                # show form errors before formset errors
                return JsonResponse(form.errors, status=400)
            else:
                # only show formset errors if there are no form errors
                # because it is unclear how to combine form and formset errors in a way that doesnt break project.js:handleFormError()
                return JsonResponse(formset.errors, status=400, safe=False)
        else:
            return self.render_to_response(
                self.get_context_data(form=form, link_formset=formset)
            )

    def get_success_url(self):
        return reverse("cruises:ajax_cruises_detail", args=(self.object.id,))


class CruiseAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Cruise
    template_name = "cruises/ajax_cruise_confirm_delete.html"
    permission_required = "cruises.delete_cruise"
    redirect_field_name = "home"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            "message": "Successfully submitted form data.",
            "parent_id": self.object.cruise_start_date.year,
            "parent_type": "year_group",
            "object_type": self.object.get_object_type(),
        }
        self.object.delete()

        return JsonResponse(data)


# Vessel CBV views
# ----------------------


class VesselListView(LoginRequiredMixin, ListView):
    model = Vessel
    template_name = "cruises/vessel_list.html"
    context_object_name = "vessels"


class VesselCreateView(LoginRequiredMixin, CreateView):
    model = Vessel
    form_class = VesselForm
    context_object_name = "vessel"
    redirect_field_name = "home"

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = VesselHyperlinkFormset(instance=self.object)
        return self.render_to_response(
            self.get_context_data(form=form, link_formset=link_formset)
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = VesselHyperlinkFormset(self.request.POST, instance=self.object)

        if form.is_valid() and link_formset.is_valid():
            return self.form_valid(form, link_formset)
        return self.form_invalid(form, link_formset)

    def form_valid(self, form, formset):
        self.object = form.save()

        data = dict(updated_values=dict())
        for field in form.fields:
            val = getattr(self.object, field, None)
            if val:
                data["updated_values"][field] = {"from": None, "to": str(val)}
        _create_action_history(self.object, Action.ADD, self.request.user, data=data)

        for link_form in formset:
            link = link_form.save(commit=False)
            if link.text and link.url:
                link.parent = self.object
                link.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, formset):
        return self.render_to_response(
            self.get_context_data(form=form, link_formset=formset)
        )

    def get_success_url(self):
        return reverse(
            "cruises:vessels_home",
        )


class VesselUpdateView(LoginRequiredMixin, UpdateView):
    model = Vessel
    form_class = VesselForm
    context_object_name = "vessel"
    redirect_field_name = "home"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = VesselHyperlinkFormset(instance=self.object)
        return self.render_to_response(
            self.get_context_data(form=form, link_formset=link_formset)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = VesselHyperlinkFormset(self.request.POST, instance=self.object)

        if form.is_valid() and link_formset.is_valid():
            return self.form_valid(form, link_formset)
        return self.form_invalid(form, link_formset)

    def form_valid(self, form, link_formset):
        orig_obj = Vessel.objects.get(pk=self.object.pk)
        new_obj = form.save(commit=False)

        data = dict(updated_values=dict())
        for field in form.fields:
            orig_val = getattr(orig_obj, field, None)
            new_val = getattr(new_obj, field, None)
            if orig_val != new_val:
                data["updated_values"][field] = {
                    "from": str(orig_val),
                    "to": str(new_val),
                }
        self.object = form.save(commit=True)
        _create_action_history(self.object, Action.UPDATE, self.request.user, data=data)

        for link_form in link_formset:
            link = link_form.save(commit=False)
            if link.text and link.url:
                if link_form["DELETE"].data:
                    link.delete()
                else:
                    link.parent = self.object
                    link.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, vessel_form, link_formset):
        return self.render_to_response(
            self.get_context_data(form=vessel_form, link_formset=link_formset)
        )

    def get_success_url(self):
        return reverse(
            "cruises:vessels_home",
        )


class VesselDeleteView(LoginRequiredMixin, DeleteView):
    model = Vessel
    success_url = reverse_lazy("cruises:vessels_home")
    redirect_field_name = "home"



class VesselActionTableView(LoginRequiredMixin, ExportMixin, SingleTableMixin, TemplateView):
    template_name = 'cruises/vessel_actionhistory.html'
    table_class = VesselActionTable
    export_name = "vessel_actionhistory__{vessel}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vessel = Vessel.objects.get(pk=self.kwargs.get('pk'))
        context['vessel'] = vessel

        return context

    def get_table_data(self):
        vessel_pk = self.kwargs.get("pk")
        qs = Action.objects.filter(vessel__pk__exact=vessel_pk)
        return qs

    def get_export_filename(self, export_format):
        vessel = Vessel.objects.get(pk=self.kwargs['pk'])
        vessel_name = str(vessel).replace('/','').replace(' ','_')
        export_name = self.export_name.format(vessel=vessel_name)
        return "{}.{}".format(export_name, export_format)
