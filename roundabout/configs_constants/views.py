from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from .models import ConfigEvent, ConfigName, ConfigValue, ConstDefault, ConstDefaultEvent
from .forms import ConfigEventForm, ConfigEventValueFormset, PartConfigNameFormset, ConfigNameForm, ConstDefaultForm, EventDefaultFormset, ConstDefaultEventForm, ConfigValueForm
from common.util.mixins import AjaxFormMixin
from django.urls import reverse, reverse_lazy
from roundabout.parts.models import Part
from roundabout.parts.forms import PartForm
from roundabout.users.models import User
from roundabout.inventory.models import Inventory, Action
from django.core import validators
from sigfig import round
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from roundabout.inventory.utils import _create_action_history

# Handles creation of Configuration / Constant Events, along with Name/Value formsets
class ConfigEventValueAdd(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = ConfigEvent
    form_class = ConfigEventForm
    context_object_name = 'event_template'
    template_name='configs_constants/config_event_value_form.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        inv_inst = Inventory.objects.get(id=self.kwargs['pk'])
        const_names = ConstDefault.objects.filter(const_event=inv_inst.constant_default_events.first())
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        ConfigEventValueAddFormset = inlineformset_factory(
            ConfigEvent, 
            ConfigValue, 
            form=ConfigValueForm,
            fields=('config_name', 'config_value', 'notes'), 
            extra=len(const_names),  
            can_delete=True
        )
        config_event_value_form = ConfigEventValueAddFormset(
            instance=self.object
        )
        for idx,name in enumerate(const_names):
            config_event_value_form.forms[idx].initial = {
                'config_name': name.config_name,
                'config_value': name.default_value
            }
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
        form.save()
        if form.cleaned_data['user_draft'].exists():
            draft_users = form.cleaned_data['user_draft']
            for user in draft_users:
                form.instance.user_draft.add(user)
        latest_deploy_date = form.instance.deployment.get_latest_deployment_date()
        if latest_deploy_date:
            form.instance.configuration_date = latest_deploy_date
        self.object = form.save()
        config_event_value_form.instance = self.object
        config_event_value_form.save()
        _create_action_history(self.object, Action.ADD, self.request.user)
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
        const_names = ConfigName.objects.filter(part=self.object.inventory.part, config_type='cnst')
        const_event = self.object.inventory.constant_default_events.first()
        event_default_names = [default for default in const_event.constant_defaults.all()]
        extra_rows = len(const_names) - len(event_default_names)
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        ConfigEventValueAddFormset = inlineformset_factory(
            ConfigEvent, 
            ConfigValue, 
            form=ConfigValueForm,
            fields=('config_name', 'config_value', 'notes'), 
            extra=extra_rows,  
            can_delete=True
        )
        config_event_value_form = ConfigEventValueAddFormset(
            instance=self.object
        )
        for idx,name in enumerate(event_default_names):
            config_event_value_form.forms[idx].initial = {
                'config_name': name.config_name,
                'config_value': name.default_value
            }
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
        form.instance.inventory = self.object.inventory
        form.instance.approved = False
        if form.cleaned_data['user_draft'].exists():
            draft_users = form.cleaned_data['user_draft']
            for user in draft_users:
                form.instance.user_draft.add(user)
                form.instance.user_approver.remove(user)
        latest_deploy_date = form.instance.deployment.get_latest_deployment_date()
        if latest_deploy_date:
            form.instance.configuration_date = latest_deploy_date
        self.object = form.save()
        config_event_value_form.instance = self.object
        config_event_value_form.save()
        _create_action_history(self.object, Action.UPDATE, self.request.user)
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


# Handles creation of Constant Defaults for Parts
class EventDefaultAdd(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = ConstDefaultEvent
    form_class = ConstDefaultEventForm
    context_object_name = 'event_template'
    template_name='configs_constants/event_default_form.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        inv_inst = Inventory.objects.get(id=self.kwargs['pk'])
        const_names = ConfigName.objects.filter(part=inv_inst.part, config_type='cnst')
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        EventDefaultAddFormset = inlineformset_factory(
            ConstDefaultEvent, 
            ConstDefault, 
            form=ConstDefaultForm,
            fields=('config_name', 'default_value'), 
            extra=len(const_names), 
            can_delete=True
        )
        event_default_form = EventDefaultAddFormset(
            instance=self.object
        )
        for idx,name in enumerate(const_names):
            event_default_form.forms[idx].initial = {'config_name': name}
        return self.render_to_response(
            self.get_context_data(
                form=form,
                event_default_form=event_default_form,
                inv_id=self.kwargs['pk']
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        event_default_form = EventDefaultFormset(
            self.request.POST, 
            instance=self.object
        )
        if (form.is_valid() and event_default_form.is_valid()):
            return self.form_valid(form, event_default_form)
        return self.form_invalid(form, event_default_form)

    def form_valid(self, form, event_default_form):
        inv_inst = Inventory.objects.get(id=self.kwargs['pk'])
        form.instance.inventory = inv_inst
        form.save()
        if form.cleaned_data['user_draft'].exists():
            draft_users = form.cleaned_data['user_draft']
            for user in draft_users:
                form.instance.user_draft.add(user)
        self.object = form.save()
        event_default_form.instance = self.object
        event_default_form.save()
        _create_action_history(self.object, Action.ADD, self.request.user)
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

    def form_invalid(self, form, event_default_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(
                    data, 
                    status=400,
                    safe=False
                )
            if event_default_form.errors:
                data = event_default_form.errors
                return JsonResponse(
                    data, 
                    status=400,
                    safe=False
                )
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    event_default_form=event_default_form, 
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.kwargs['pk'], ))


# Handles creation of Constant Defaults for Parts
class EventDefaultUpdate(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = ConstDefaultEvent
    form_class = ConstDefaultEventForm
    context_object_name = 'event_template'
    template_name='configs_constants/event_default_form.html'
    permission_required = 'configs_constants.add_constantdefaultevent'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        const_names = ConfigName.objects.filter(part=self.object.inventory.part, config_type='cnst')
        event_default_names = [default.config_name for default in self.object.constant_defaults.all()]
        extra_rows = len(const_names) - len(event_default_names)
        EventDefaultAddFormset = inlineformset_factory(
            ConstDefaultEvent, 
            ConstDefault, 
            form=ConstDefaultForm,
            fields=('config_name', 'default_value'), 
            extra=extra_rows, 
            can_delete=True
        )
        event_default_form = EventDefaultAddFormset(
            instance=self.object
        )
        for idx,name in enumerate(const_names):
            event_default_form.forms[idx].initial = {'config_name': name}
        return self.render_to_response(
            self.get_context_data(
                form=form,
                event_default_form=event_default_form,
                inv_id=self.object.inventory.id
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        event_default_form = EventDefaultFormset(
            self.request.POST, 
            instance=self.object
        )
        if (form.is_valid() and event_default_form.is_valid()):
            return self.form_valid(form, event_default_form)
        return self.form_invalid(form, event_default_form)

    def form_valid(self, form, event_default_form):
        form.instance.inventory = self.object.inventory
        form.instance.approved = False
        if form.cleaned_data['user_draft'].exists():
            draft_users = form.cleaned_data['user_draft']
            for user in draft_users:
                form.instance.user_draft.add(user)
                form.instance.user_approver.remove(user)
        self.object = form.save()
        event_default_form.instance = self.object
        event_default_form.save()
        _create_action_history(self.object, Action.UPDATE, self.request.user)
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

    def form_invalid(self, form, event_default_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(
                    data, 
                    status=400,
                    safe=False
                )
            if event_default_form.errors:
                data = event_default_form.errors
                return JsonResponse(
                    data, 
                    status=400,
                    safe=False
                )
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    event_default_form=event_default_form, 
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.object.inventory.id, ))


# Handles deletion of Events
class EventDefaultDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ConstDefaultEvent
    context_object_name='event_template'
    template_name = 'configs_constants/config_event_delete.html'
    permission_required = 'configs_constants.add_constantdefaultevent'
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


# Swap reviewers to approvers
def event_constdefault_approve(request, pk, user_pk):
    event = ConstDefaultEvent.objects.get(id=pk)
    user = User.objects.get(id=user_pk)
    reviewers = event.user_draft.all()
    if user in reviewers:
        event.user_draft.remove(user)
        event.user_approver.add(user)
        _create_action_history(event, Action.REVIEWAPPROVE, user)
    if len(event.user_draft.all()) == 0:
        event.approved = True
        _create_action_history(event, Action.EVENTAPPROVE, user)
    event.save()
    data = {'approved':event.approved}
    return JsonResponse(data)

# Swap reviewers to approvers
def event_value_approve(request, pk, user_pk):
    event = ConfigEvent.objects.get(id=pk)
    user = User.objects.get(id=user_pk)
    reviewers = event.user_draft.all()
    if user in reviewers:
        event.user_draft.remove(user)
        event.user_approver.add(user)
        _create_action_history(event, Action.REVIEWAPPROVE, user)
    if len(event.user_draft.all()) == 0:
        event.approved = True
        _create_action_history(event, Action.EVENTAPPROVE, user)
    event.save()
    data = {'approved':event.approved}
    return JsonResponse(data)