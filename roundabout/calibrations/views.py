from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from .models import CoefficientName, CalibrationEvent, CoefficientValueSet
from .forms import CalibrationEventForm, EventValueSetFormset, CoefficientValueForm, CoefficientValueSetForm, ValueSetValueFormset, CoefficientNameForm, PartCalNameFormset
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

# Handles creation of Calibration Events, Names,and Coefficients
class EventValueSetAdd(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = CalibrationEvent
    form_class = CalibrationEventForm
    context_object_name = 'event_template'
    template_name='calibrations/event_valueset_form.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        event_valueset_form = EventValueSetFormset(
            instance=self.object, 
            form_kwargs={'inv_id': self.kwargs['pk']}
        )
        return self.render_to_response(
            self.get_context_data(
                form=form, 
                event_valueset_form=event_valueset_form
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        event_valueset_form = EventValueSetFormset(
            self.request.POST, 
            instance=self.object,
            form_kwargs={'inv_id': self.kwargs['pk']}
        )
        if (form.is_valid() and event_valueset_form.is_valid()):
            return self.form_valid(form, event_valueset_form)
        return self.form_invalid(form, event_valueset_form)

    def form_valid(self, form, event_valueset_form):
        inv_inst = Inventory.objects.get(id=self.kwargs['pk'])
        form.instance.inventory = inv_inst
        if form.cleaned_data['approved']:
            form.instance.user_approver = self.request.user
        if form.cleaned_data['user_draft'].exists():
            form.instance.user_draft.set(form.cleaned_data['user_draft'])
        self.object = form.save()
        event_valueset_form.instance = self.object
        event_valueset_form.save(commit=False)
        for val in event_valueset_form:
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

    def form_invalid(self, form, event_valueset_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(data, status=400)
            elif event_valueset_form.errors:
                print('coeffcreateform errors')
                data = event_valueset_form.errors
                return JsonResponse(data, status=400, safe=False)
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form, 
                    event_valueset_form=event_valueset_form, 
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.kwargs['pk'], ))

# Handles updating of Calibration Events, Names, and Coefficients
class EventValueSetUpdate(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = CalibrationEvent
    form_class = CalibrationEventForm
    context_object_name = 'event_template'
    template_name='calibrations/event_valueset_form.html'
    permission_required = 'calibrations.add_calibrationevent'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        event_valueset_form = EventValueSetFormset(
            instance=self.object, 
            form_kwargs={'inv_id': self.object.inventory.id}
        )
        return self.render_to_response(
            self.get_context_data(
                form=form, 
                event_valueset_form=event_valueset_form
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        event_valueset_form = EventValueSetFormset(
            self.request.POST, 
            instance=self.object, 
            form_kwargs={'inv_id': self.object.inventory.id}
        )
        if (form.is_valid() and event_valueset_form.is_valid()):
            return self.form_valid(form, event_valueset_form)
        return self.form_invalid(form, event_valueset_form)

    def form_valid(self, form, event_valueset_form):
        inv_inst = Inventory.objects.get(id=self.object.inventory.id)
        form.instance.inventory = inv_inst
        if form.cleaned_data['approved']:
            form.instance.user_approver = self.request.user
        if form.cleaned_data['user_draft'].exists():
            form.instance.user_draft.set(form.cleaned_data['user_draft'])
        self.object = form.save()
        event_valueset_form.instance = self.object
        event_valueset_form.save(commit=False)
        for val in event_valueset_form:
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

    def form_invalid(self, form, event_valueset_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(
                    data, 
                    status=400
                )
            if event_valueset_form.errors:
                print('coeffupdateform errors')
                data = event_valueset_form.errors
                return JsonResponse(
                    data, 
                    status=400,
                    safe=False
                )
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form, 
                    event_valueset_form=event_valueset_form, 
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.object.inventory.id, ))


# Handles deletion of Events
class EventValueSetDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = CalibrationEvent
    context_object_name='event_template'
    template_name = 'calibrations/event_delete.html'
    permission_required = 'calibrations.add_calibrationevent'
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



# Handles updating of CoefficientValueSet Values
class ValueSetValueUpdate(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = CoefficientValueSet
    form_class = CoefficientValueSetForm
    context_object_name = 'valueset_template'
    template_name='calibrations/valueset_value_form.html'
    permission_required = 'calibrations.add_coefficientvalue'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        valueset_value_form = ValueSetValueFormset(
            instance=self.object,
            form_kwargs={'valset_id': self.object.id}
        )
        return self.render_to_response(
            self.get_context_data(
                valueset_value_form=valueset_value_form
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        valueset_value_form = ValueSetValueFormset(
            self.request.POST, 
            instance=self.object,
            form_kwargs={'valset_id': self.object.id}
        )
        if (valueset_value_form.is_valid()):
            return self.form_valid(valueset_value_form)
        return self.form_invalid(valueset_value_form)

    def form_valid(self, valueset_value_form):
        valueset_value_form.instance = self.object
        valueset_value_form.save()
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

    def form_invalid(self, valueset_value_form):
        if self.request.is_ajax():
            if valueset_value_form.errors:
                print('coeffupdateform errors')
                data = valueset_value_form.errors
                return JsonResponse(
                    data, 
                    status=400,
                    safe=False
                )
        else:
            return self.render_to_response(
                self.get_context_data(
                    valueset_value_form=valueset_value_form, 
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.object.calibration_event.inventory.id, ))


# Handles creation of Calibration Names for Parts
class PartCalNameAdd(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = Part
    form_class = PartForm
    context_object_name = 'part_template'
    template_name='calibrations/part_calname_form.html'
    permission_required = 'calibrations.add_coefficientname'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        part_calname_form = PartCalNameFormset(
            instance=self.object
        )
        return self.render_to_response(
            self.get_context_data(
                part_calname_form=part_calname_form
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        part_calname_form = PartCalNameFormset(
            self.request.POST, 
            instance=self.object
        )
        if (part_calname_form.is_valid()):
            return self.form_valid(part_calname_form)
        return self.form_invalid(part_calname_form)

    def form_valid(self, part_calname_form):
        part_calname_form.instance = self.object
        part_calname_form.save()
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

    def form_invalid(self, part_calname_form):
        if self.request.is_ajax():
            if part_calname_form.errors:
                print('partcalnameupdate errors')
                data = part_calname_form.errors
                return JsonResponse(
                    data, 
                    status=400,
                    safe=False
                )
        else:
            return self.render_to_response(
                self.get_context_data(
                    part_calname_form=part_calname_form, 
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('parts:ajax_parts_detail', args=(self.object.id, ))

def test_view(request, pk, user_pk):
    event = CalibrationEvent.objects.get(id=pk)
    user = User.objects.get(id=user_pk)
    reviewers = event.user_draft.all()
    if user in reviewers:
        reviewers_minus_user = reviewers.exclude(username=user)
        event.user_draft.set(reviewers_minus_user)
    data = {'data': 'success'}
    return JsonResponse(data)