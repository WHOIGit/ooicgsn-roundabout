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

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from .models import CoefficientName, CalibrationEvent, CoefficientValueSet, CoefficientNameEvent
from .forms import CalibrationEventForm, EventValueSetFormset, CoefficientValueForm, CoefficientValueSetForm, ValueSetValueFormset, CoefficientNameForm, PartCalNameFormset, CalPartCopyForm, CoefficientNameEventForm
from common.util.mixins import AjaxFormMixin
from django.urls import reverse, reverse_lazy
from roundabout.parts.models import Part
from roundabout.parts.forms import PartForm
from roundabout.users.models import User
from roundabout.inventory.models import Inventory, Action
from roundabout.inventory.utils import _create_action_history
from django.core import validators
from sigfig import round
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from .utils import handle_reviewers
from .tasks import check_events

# Handles creation of Calibration Events, Names,and Coefficients
class EventValueSetAdd(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = CalibrationEvent
    form_class = CalibrationEventForm
    context_object_name = 'event_template'
    template_name='calibrations/event_valueset_form.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        inv_inst = Inventory.objects.get(id=self.kwargs['pk'])
        coeff_event = inv_inst.part.coefficient_name_events.first()
        cal_names = coeff_event.coefficient_names.exclude(deprecated=True)
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        form.fields['user_draft'].required = True
        EventValueSetAddFormset = inlineformset_factory(
            CalibrationEvent,
            CoefficientValueSet,
            form=CoefficientValueSetForm,
            fields=('coefficient_name', 'value_set', 'notes'),
            extra=len(cal_names),
            can_delete=True
        )
        event_valueset_form = EventValueSetAddFormset(
            instance=self.object,
            form_kwargs={'inv_id': self.kwargs['pk']}
        )
        for idx,name in enumerate(cal_names):
            event_valueset_form.forms[idx].initial = {'coefficient_name': name}
        return self.render_to_response(
            self.get_context_data(
                form=form,
                event_valueset_form=event_valueset_form,
                inv_id = self.kwargs['pk']
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
        form.save()
        if form.cleaned_data['user_draft'].exists():
            draft_users = form.cleaned_data['user_draft']
            for user in draft_users:
                form.instance.user_draft.add(user)
        self.object = form.save()
        event_valueset_form.instance = self.object
        event_valueset_form.save()
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

    def form_invalid(self, form, event_valueset_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(data, status=400)
            elif event_valueset_form.errors:
                data = event_valueset_form.errors
                return JsonResponse(data, status=400, safe=False)
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    event_valueset_form=event_valueset_form,
                    form_errors=form_errors,
                    inv_id = self.kwargs['pk']
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
        form.fields['user_draft'].required = False
        event_valueset_form = EventValueSetFormset(
            instance=self.object,
            form_kwargs={'inv_id': self.object.inventory.id}
        )
        return self.render_to_response(
            self.get_context_data(
                form=form,
                event_valueset_form=event_valueset_form,
                inv_id = self.object.inventory.id
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
        form.instance.approved = False
        handle_reviewers(form)
        self.object = form.save()
        event_valueset_form.instance = self.object
        event_valueset_form.save()
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

    def form_invalid(self, form, event_valueset_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(
                    data,
                    status=400
                )
            if event_valueset_form.errors:
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
                    form_errors=form_errors,
                    inv_id = self.object.inventory.id
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
        return reverse('inventory:ajax_inventory_detail', args=(self.object.inventory.id,))


def event_delete_view(request, pk):
    evt = CalibrationEvent.objects.get(id=pk)
    inv_id = evt.inventory.id
    if request.method == "POST":
        evt.delete()
        return HttpResponseRedirect(reverse('inventory:ajax_inventory_detail', args=(inv_id,)))
        
    return render(request, 'calibrations/event_delete.html', {
        "event_template": evt,
        'request': request
    })



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
class EventCoeffNameAdd(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = CoefficientNameEvent
    form_class = CoefficientNameEventForm
    context_object_name = 'event_template'
    template_name='calibrations/part_calname_form.html'
    permission_required = 'calibrations.add_coefficientname'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        part_id = self.kwargs['pk']
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        form.fields['user_draft'].required = True
        part_calname_form = PartCalNameFormset(
            instance=self.object
        )
        part_cal_copy_form = CalPartCopyForm(
            part_id = part_id
        )

        return self.render_to_response(
            self.get_context_data(
                part_id=part_id,
                form=form,
                part_calname_form=part_calname_form,
                part_cal_copy_form=part_cal_copy_form
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        part_calname_form = PartCalNameFormset(
            self.request.POST,
            instance=self.object
        )
        part_cal_copy_form = CalPartCopyForm(
            self.request.POST,
            part_id = self.kwargs['pk']
        )
        if (form.is_valid() and part_calname_form.is_valid() and part_cal_copy_form.is_valid()):
            return self.form_valid(form, part_calname_form, part_cal_copy_form)
        return self.form_invalid(form, part_calname_form, part_cal_copy_form)

    def form_valid(self, form, part_calname_form, part_cal_copy_form):
        form.instance.part = Part.objects.get(id=self.kwargs['pk'])
        form.save()
        if form.cleaned_data['user_draft'].exists():
            draft_users = form.cleaned_data['user_draft']
            for user in draft_users:
                form.instance.user_draft.add(user)
        self.object = form.save()
        part_calname_form.instance = self.object
        part_calname_form.save()
        part_cal_copy_form.save()
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

    def form_invalid(self, form, part_calname_form, part_cal_copy_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(
                    data,
                    status=400,
                    safe=False
                )
            if part_cal_copy_form.errors:
                data = part_cal_copy_form.errors
                return JsonResponse(
                    data,
                    status=400,
                    safe=False
                )
            if part_calname_form.errors:
                data = part_calname_form.errors
                return JsonResponse(
                    data,
                    status=400,
                    safe=False
                )
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    part_calname_form=part_calname_form,
                    part_cal_copy_form=part_cal_copy_form,
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('parts:ajax_parts_detail', args=(self.object.part.id, ))


# Handles editing of Calibration Names for Parts
class EventCoeffNameUpdate(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = CoefficientNameEvent
    form_class = CoefficientNameEventForm
    context_object_name = 'event_template'
    template_name='calibrations/part_calname_form.html'
    permission_required = 'calibrations.add_coefficientname'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        part_id = self.object.part.id
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        form.fields['user_draft'].required = False
        part_calname_form = PartCalNameFormset(
            instance=self.object
        )
        part_cal_copy_form = CalPartCopyForm(
            part_id = part_id
        )

        return self.render_to_response(
            self.get_context_data(
                part_id=part_id,
                form=form,
                part_calname_form=part_calname_form,
                part_cal_copy_form=part_cal_copy_form
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
        part_cal_copy_form = CalPartCopyForm(
            self.request.POST,
            part_id = self.object.part.id
        )
        if (form.is_valid() and part_calname_form.is_valid() and part_cal_copy_form.is_valid()):
            return self.form_valid(form, part_calname_form, part_cal_copy_form)
        return self.form_invalid(form, part_calname_form, part_cal_copy_form)

    def form_valid(self, form, part_calname_form, part_cal_copy_form):
        form.instance.part = self.object.part
        form.instance.approved = False
        form.save()
        handle_reviewers(form)
        self.object = form.save()
        part_calname_form.instance = self.object
        part_calname_form.save()
        part_cal_copy_form.save()
        _create_action_history(self.object, Action.UPDATE, self.request.user)
        job = check_events.delay()
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

    def form_invalid(self, form, part_calname_form, part_cal_copy_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(
                    data,
                    status=400,
                    safe=False
                )
            if part_cal_copy_form.errors:
                data = part_cal_copy_form.errors
                return JsonResponse(
                    data,
                    status=400,
                    safe=False
                )
            if part_calname_form.errors:
                data = part_calname_form.errors
                return JsonResponse(
                    data,
                    status=400,
                    safe=False
                )
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    part_calname_form=part_calname_form,
                    part_cal_copy_form=part_cal_copy_form,
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('parts:ajax_parts_detail', args=(self.object.part.id, ))


# Handles deletion of CoefficientNameEvents
class EventCoeffNameDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = CoefficientNameEvent
    context_object_name='event_template'
    template_name = 'calibrations/event_calname_delete.html'
    permission_required = 'calibrations.add_calibrationevent'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.part.id,
            'parent_type': 'part_type',
            'object_type': self.object.get_object_type(),
        }
        self.object.delete()
        job = check_events.delay()
        return JsonResponse(data)

    def get_success_url(self):
        return reverse_lazy('parts:ajax_part_detail', args=(self.object.part.id, ))


# Swap reviewers to approvers
def event_review_approve(request, pk, user_pk):
    event = CalibrationEvent.objects.get(id=pk)
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
def event_coeffname_approve(request, pk, user_pk):
    event = CoefficientNameEvent.objects.get(id=pk)
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