from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from .models import ConfigEvent, ConfigName, ConfigValue
from .forms import ConfigEventForm, ConfigEventValueFormset, PartConfigNameFormset
from common.util.mixins import AjaxFormMixin
from django.urls import reverse, reverse_lazy
from roundabout.parts.models import Part
from roundabout.parts.forms import PartForm
from roundabout.users.models import User
from roundabout.inventory.models import Inventory
from django.core import validators
from sigfig import round
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Handles creation of Configuration / Constant Events, along with Name/Value formsets
class ConfigEventValueAdd(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = ConfigEvent
    form_class = ConfigEventForm
    context_object_name = 'event_template'
    template_name='configs_constants/config_event_value_form.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        config_event_value_form = ConfigEventValueFormset(
            instance=self.object
        )
        return self.render_to_response(
            self.get_context_data(
                form=form, 
                config_event_value_form=config_event_value_form
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        config_event_value_form = ConfigEventValueFormset(
            self.request.POST, 
            instance=self.object
        )
        if (form.is_valid() and config_event_value_form.is_valid()):
            return self.form_valid(form, config_event_value_form)
        return self.form_invalid(form, config_event_value_form)

    def form_valid(self, form, config_event_value_form):
        inv_inst = Inventory.objects.get(id=self.kwargs['pk'])
        form.instance.inventory = inv_inst
        if form.cleaned_data['approved']:
            form.instance.user_approver = self.request.user
        form.instance.user_draft = self.request.user
        deploy_info = form.instance.deployment.get_deploytosea_details()
        if deploy_info:
            form.instance.configuration_date = deploy_info['deploy_date']
        self.object = form.save()
        config_event_value_form.instance = self.object
        config_event_value_form.save()
        response = HttpResponseRedirect(self.get_success_url())
        if self.request.is_ajax():
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def form_invalid(self, form, config_event_value_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(data, status=400)
            elif config_event_value_form.errors:
                data = config_event_value_form.errors
                return JsonResponse(data, status=400, safe=False)
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form, 
                    config_event_value_form=config_event_value_form, 
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.kwargs['pk'], ))

# Handles updating of Config / Constant forms
class ConfigEventValueUpdate(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = ConfigEvent
    form_class = ConfigEventForm
    context_object_name = 'event_template'
    template_name='configs_constants/config_event_value_form.html'
    permission_required = 'configs_constants.add_configevent'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        config_event_value_form = ConfigEventValueFormset(
            instance=self.object
        )
        return self.render_to_response(
            self.get_context_data(
                form=form, 
                config_event_value_form=config_event_value_form
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        config_event_value_form = ConfigEventValueFormset(
            self.request.POST, 
            instance=self.object
        )
        if (form.is_valid() and config_event_value_form.is_valid()):
            return self.form_valid(form, config_event_value_form)
        return self.form_invalid(form, config_event_value_form)

    def form_valid(self, form, config_event_value_form):
        inv_inst = Inventory.objects.get(id=self.object.inventory.id)
        form.instance.inventory = inv_inst
        if form.cleaned_data['approved']:
            form.instance.user_approver = self.request.user
        form.instance.user_draft = self.request.user
        deploy_info = form.instance.deployment.get_deploytosea_details()
        if deploy_info:
            form.instance.configuration_date = deploy_info['deploy_date']
        self.object = form.save()
        config_event_value_form.instance = self.object
        config_event_value_form.save(commit=False)
        for val in config_event_value_form:
            if val.has_changed():
                val.save()
        response = HttpResponseRedirect(self.get_success_url())
        if self.request.is_ajax():
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def form_invalid(self, form, config_event_value_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(
                    data, 
                    status=400
                )
            if config_event_value_form.errors:
                data = config_event_value_form.errors
                return JsonResponse(
                    data, 
                    status=400,
                    safe=False
                )
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form, 
                    config_event_value_form=config_event_value_form, 
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.object.inventory.id, ))

# Handles deletion of Configuration Events
class ConfigEventValueDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ConfigEvent
    context_object_name='event_template'
    template_name = 'configs_constants/config_event_delete.html'
    permission_required = 'configs_constants.add_configevent'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.inventory.id,
            'parent_type': 'part_type',
            'object_type': self.object.get_object_type(),
        }
        self.object.delete()
        return JsonResponse(data)

    def get_success_url(self):
        return reverse_lazy('inventory:ajax_inventory_detail', args=(self.object.inventory.id, ))

# Handles creation of Configuration Names for Parts
class PartConfNameAdd(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = Part
    form_class = PartForm
    context_object_name = 'part_template'
    template_name='configs_constants/part_confname_form.html'
    permission_required = 'configs_constants.add_configname'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        part_confname_form = PartConfigNameFormset(
            instance=self.object
        )
        return self.render_to_response(
            self.get_context_data(
                part_confname_form=part_confname_form
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        part_confname_form = PartConfigNameFormset(
            self.request.POST, 
            instance=self.object
        )
        if (part_confname_form.is_valid()):
            return self.form_valid(part_confname_form)
        return self.form_invalid(part_confname_form)

    def form_valid(self, part_confname_form):
        part_confname_form.instance = self.object
        part_confname_form.save()
        response = HttpResponseRedirect(self.get_success_url())
        if self.request.is_ajax():
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def form_invalid(self, part_confname_form):
        if self.request.is_ajax():
            if part_confname_form.errors:
                data = part_confname_form.errors
                return JsonResponse(
                    data, 
                    status=400,
                    safe=False
                )
        else:
            return self.render_to_response(
                self.get_context_data(
                    part_confname_form=part_confname_form, 
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('parts:ajax_parts_detail', args=(self.object.id, ))