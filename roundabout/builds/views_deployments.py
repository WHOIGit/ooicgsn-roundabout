from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from common.util.mixins import AjaxFormMixin
from .models import Build, BuildAction
from .forms import *
from roundabout.locations.models import Location
from roundabout.inventory.models import Inventory, Action, Deployment

## CBV views for Builds app ##

# Create Deployment for Build
class DeploymentAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Deployment
    form_class = DeploymentForm
    context_object_name = 'deployment'
    template_name='builds/ajax_deployment_form.html'

    def get_initial(self):
        #Returns the initial data to use for forms on this view.
        initial = super(DeploymentAjaxCreateView, self).get_initial()
        if 'build_pk' in self.kwargs:
            build = Build.objects.get(id=self.kwargs['build_pk'])
            initial['build'] = build
            initial['location'] = build.location
        return initial

    def get_success_url(self):
        return reverse('deployments:ajax_deployment_detail', args=(self.object.id,))

    def form_valid(self, form):
        self.object = form.save()
        build = self.object.build
        build.is_deployed = True
        build.save()

        # Get the date for the Action Record from the custom form field
        action_date = form.cleaned_data['date']
        action_record = DeploymentAction.objects.create(action_type='create', detail='Deployment created', location_id=self.object.location_id,
                                              user_id=self.request.user.id, deployment_id=self.object.id, created_at=action_date)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.build.id,
            }
            return JsonResponse(data)
        else:
            return response
