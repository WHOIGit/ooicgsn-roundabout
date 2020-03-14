from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from .models import CoefficientName
from .forms import CalibrationAddForm
from common.util.mixins import AjaxFormMixin
from django.urls import reverse, reverse_lazy

# Calibraitons landing page
class CalibrationsAddView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = CoefficientName
    form_class = CalibrationAddForm
    context_object_name = 'calibration_item'
    template_name ='calibrations/calibrations_form.html'

    def get_context_data(self, **kwargs):
        context = super(CalibrationsAddView, self).get_context_data(**kwargs)
        context.update({
            'node_type': 'calibrations'
        })
        return context

    def get_success_url(self):
        return reverse('calibrations:calibrations_form')

    def form_valid(self, form):
        self.object = form.save()

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