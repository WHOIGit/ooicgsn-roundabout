from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, UpdateView
from .models import CoefficientName, CalibrationEvent
from .forms import CalibrationAddForm, CoefficientFormset, CoefficientValueForm
from common.util.mixins import AjaxFormMixin
from django.urls import reverse, reverse_lazy
from roundabout.parts.models import Part
from roundabout.users.models import User
from roundabout.inventory.models import Inventory
from django.core import validators
from sigfig import round

# Handles creation of Calibration Events, Names,and Coefficients
class CalibrationsAddView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = CalibrationEvent
    form_class = CalibrationAddForm
    context_object_name = 'event_template'
    template_name='calibrations/calibrations_form.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        coefficient_form = CoefficientFormset(instance=self.object, form_kwargs={'inv_id': self.kwargs['pk']})
        return self.render_to_response(self.get_context_data(form=form, coefficient_form=coefficient_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        coefficient_form = CoefficientFormset(self.request.POST, instance=self.object)
        if (form.is_valid() and coefficient_form.is_valid()):
            return self.form_valid(form, coefficient_form)
        return self.form_invalid(form, coefficient_form)

    def form_valid(self, form, coefficient_form):
        inv_inst = Inventory.objects.get(id=self.kwargs['pk'])
        form.instance.inventory = inv_inst
        if form.cleaned_data['approved']:
            form.instance.user_approver = self.request.user
        form.instance.user_draft = self.request.user
        self.object = form.save()
        coefficient_form.instance = self.object
        for form in coefficient_form:
            form_coeff_val = form.cleaned_data.get('value')
            form_notation_format = form.cleaned_data.get('notation_format')
            part_dec_places = inv_inst.part.cal_dec_places
            calibration_name = form.cleaned_data.get('coefficient_name')
            if calibration_name:    
                sigfig_formatted_value = round(form_coeff_val, sigfigs = calibration_name.sigfig, decimals = part_dec_places, notation = form_notation_format)
            else:
                sigfig_formatted_value = 0
            form.instance.value = sigfig_formatted_value
        coefficient_form.save()
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

    def form_invalid(self, form, coefficient_form):
        print('coeff_form_create_errors')
        print(form_errors)
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(data, status=400)
            if coefficient_form.errors:
                data = form.errors
                return JsonResponse(data, status=400, safe=False)
        else:
            return self.render_to_response(self.get_context_data(form=form, coefficient_form=coefficient_form, form_errors=form_errors))

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.kwargs['pk'], ))

# Handles updating of Calibration Events, Names, and Coefficients
class CalibrationsUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = CalibrationEvent
    form_class = CalibrationAddForm
    context_object_name = 'event_template'
    template_name='calibrations/calibrations_form.html'
    permission_required = 'calibrations.add_calibration'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        coefficient_form = CoefficientFormset(instance=self.object, form_kwargs={'inv_id': self.object.inventory.id})
        return self.render_to_response(self.get_context_data(form=form, coefficient_form=coefficient_form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        coefficient_form = CoefficientFormset(self.request.POST, instance=self.object)
        if (form.is_valid() and coefficient_form.is_valid()):
            return self.form_valid(form, coefficient_form)
        return self.form_invalid(form, coefficient_form)

    def form_valid(self, form, coefficient_form):
        inv_inst = Inventory.objects.get(id=self.object.inventory.id)
        form.instance.inventory = inv_inst
        if form.cleaned_data['approved']:
            form.instance.user_approver = self.request.user
        form.instance.user_draft = self.request.user
        self.object = form.save()
        coefficient_form.instance = self.object
        for form in coefficient_form:
            form_coeff_val = form.cleaned_data.get('value')
            form_notation_format = form.cleaned_data.get('notation_format')
            part_dec_places = inv_inst.part.cal_dec_places
            calibration_name = form.cleaned_data.get('coefficient_name')
            if calibration_name:    
                sigfig_formatted_value = round(form_coeff_val, sigfigs = calibration_name.sigfig, decimals = part_dec_places, notation = form_notation_format)
            else:
                sigfig_formatted_value = 0
            form.instance.value = sigfig_formatted_value
        coefficient_form.save()
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

    def form_invalid(self, form, coefficient_form):
        print('coeff_form_update_errors')
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(
                    data, 
                    status=400
                )
            if coefficient_form.errors:
                data = coefficient_form.errors
                return JsonResponse(
                    data, 
                    status=400,
                    safe=False
                )
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form, 
                    coefficient_form=coefficient_form, 
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.object.inventory.id, ))