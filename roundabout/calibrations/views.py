from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from .models import CoefficientName, CalibrationEvent
from .forms import CalibrationAddForm, CoefficientFormset
from common.util.mixins import AjaxFormMixin
from django.urls import reverse, reverse_lazy
from roundabout.parts.models import Part
from roundabout.users.models import User
from roundabout.inventory.models import Inventory

# Calibraitons landing page
class CalibrationsAddView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = CalibrationEvent
    form_class = CalibrationAddForm
    context_object_name = 'part_template'
    template_name='calibrations/calibrations_form.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        coefficient_form = CoefficientFormset(instance=self.object)

        return self.render_to_response(self.get_context_data(form=form, coefficient_form=coefficient_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        coefficient_form = CoefficientFormset(
            self.request.POST, instance=self.object)

        if (form.is_valid() and coefficient_form.is_valid()):
            return self.form_valid(form, coefficient_form)
        return self.form_invalid(form, coefficient_form)

    def form_valid(self, form, coefficient_form):
        self.object = form.save()

        # # Save CoefficientValue form using CoefficientName instance
        calibration_name = form.cleaned_data['coefficient_name']
        coeffname_inst = CoefficientName.objects.get(calibration_name=calibration_name)
        coefficient_form.coefficient_name = coeffname_inst

        inventory = coeffname_inst.part.inventory.all()
        inv_inst = inventory[0]
        event_record = CalibrationEvent.objects.create(inventory=inv_inst, user_draft=self.request.user)
        coefficient_form.instance = event_record
        coefficient_form.save()

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
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
        form_errors = coefficient_form.errors

        if self.request.is_ajax():
            data = form.errors
            return JsonResponse(data, status=400)
        else:
            return self.render_to_response(self.get_context_data(form=form, coefficient_form=coefficient_form, form_errors=form_errors))

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.kwargs['pk'], ))