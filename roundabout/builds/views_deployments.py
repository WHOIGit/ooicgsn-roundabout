from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from common.util.mixins import AjaxFormMixin
from .models import Build, BuildAction
from .forms import *
from roundabout.locations.models import Location
from roundabout.inventory.models import Inventory, Action, Deployment, DeploymentAction

## CBV views for Deployments as part of Builds app ##

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
        return reverse('builds:ajax_builds_detail', args=(self.object.build.id,))

    def form_valid(self, form):
        self.object = form.save()
        build = self.object.build
        build.is_deployed = True
        build.save()

        # Get the date for the Action Record from the custom form field
        action_date = form.cleaned_data['date']
        action_record = DeploymentAction.objects.create(action_type='create', detail='Deployment created', location=self.object.location,
                                                        user=self.request.user, deployment=self.object, created_at=action_date)

        # Create Build Action record for deployment
        build_detail = '%s Deployment started.' % (self.object.deployment_number)
        build_record = BuildAction.objects.create(action_type='startdeploy', detail=build_detail, location=self.object.location,
                                                   user=self.request.user, build=build)

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


class DeploymentAjaxUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = Deployment
    form_class = DeploymentForm
    context_object_name = 'deployment'
    template_name='builds/ajax_deployment_form.html'

    def get_context_data(self, **kwargs):
        context = super(DeploymentAjaxUpdateView, self).get_context_data(**kwargs)

        if 'action_type' in self.kwargs:
            context['action_type'] = self.kwargs['action_type']
        else:
            context['action_type'] = None

        return context

    def get_success_url(self):
        return reverse('builds:ajax_builds_detail', args=(self.object.build.id,))


class DeploymentAjaxActionView(DeploymentAjaxUpdateView):

    def get_context_data(self, **kwargs):
        context = super(DeploymentAjaxActionView, self).get_context_data(**kwargs)

        latest_action_record = DeploymentAction.objects.filter(deployment=self.object).first()

        context.update({
            'latest_action_record': latest_action_record
        })
        return context

    def get_form_class(self):
        ACTION_FORMS = {
            "burnin" : DeploymentActionBurninForm,
            "deploy" : DeploymentActionDeployForm,
            "recover" : DeploymentActionRecoverForm,
            "retire" : DeploymentActionRetireForm,
        }
        action_type = self.kwargs['action_type']
        form_class_name = ACTION_FORMS[action_type]

        return form_class_name

    def form_valid(self, form):

        action_type = self.kwargs['action_type']

        # Set Detail and action_type_inventory variables
        if action_type == 'burnin':
            self.object.detail = '%s Burn In initiated at %s. ' % (self.object.deployment_number, self.object.location)
            action_type_inventory = 'deploymentburnin'

        if action_type == 'deploy':
            self.object.detail = '%s Deployed to Sea: %s. ' % (self.object.deployment_number, self.object.location)
            action_type_inventory = 'deploymenttosea'

        if action_type == 'recover':
            self.object.detail = '%s Recovered from Sea to %s. ' % (self.object.deployment_number, self.object.location)
            action_type_inventory = 'deploymentrecover'

        if action_type == 'retire':
            self.object.detail = '%s Retired.' % (self.object.deployment_number)
            action_type_inventory = 'removefromdeployment'

        action_form = form.save()

        # Get the date for the Action Record from the custom form field
        action_date = form.cleaned_data['date']

        """
        # Create automatic Snapshot when Deployed to Sea or Recovered
        if action_type == 'deploy' or action_type == 'recover':
            # Create a Snapshot when Deployment is Deployed
            deployment = self.object
            base_location = Location.objects.get(root_type='Snapshots')
            inventory_items = deployment.inventory.all()

            snapshot = DeploymentSnapshot.objects.create(deployment=deployment,
                                                         location=base_location,
                                                         snapshot_location=deployment.location,
                                                         notes=self.object.detail,
                                                         created_at=action_date, )

            # Now create Inventory Item Snapshots with make_tree_copy function for Deployment Snapshot
            for item in inventory_items:
                if item.is_root_node():
                    make_tree_copy(item, base_location, snapshot, item.parent)
        """
        # If Deploying to Sea, add Depth, Lat/Long to Action Record
        if action_type == 'deploy':
            latitude = form.cleaned_data['latitude']
            longitude = form.cleaned_data['longitude']
            depth = form.cleaned_data['depth']
            self.object.detail =  self.object.detail + '<br> Latitude: ' + str(latitude) + '<br> Longitude: ' + str(longitude) + '<br> Depth: ' + str(depth)
        else:
            latitude = None
            longitude = None
            depth = None

        action_record = DeploymentAction.objects.create(action_type=action_type, detail=self.object.detail, location_id=self.object.location_id,
                                              user_id=self.request.user.id, deployment_id=self.object.id, created_at=action_date,
                                              latitude=latitude, longitude=longitude, depth=depth)

        # Update Build location, create Action Record
        build = self.object.build

        if action_type == 'retire':
            build.is_deployed = False
        else:
            build.location = self.object.location

        build.save()

        # Create Build Action record for deployment
        build_record = BuildAction.objects.create(action_type=action_type_inventory, detail=self.object.detail, location=self.object.location,
                                                   user=self.request.user, build=build, created_at=action_date)

        # Get all Inventory items on Deployment, match location and add Action
        inventory_items = Inventory.objects.filter(build=build)
        for item in inventory_items:
            item.location = build.location
            item.save()

            action_record = Action.objects.create(action_type=action_type_inventory, detail='', location=build.location,
                                                  user=self.request.user, inventory=item, created_at=action_date)
            action_detail = '%s, moved to %s. ' % (action_record.get_action_type_display(), self.object.location)
            action_record.detail = action_detail
            action_record.save()

            #update Time at Sea if Recovered from Sea with model method
            if action_type == 'recover':
                item.update_time_at_sea()

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': build.id,
                'location_id': self.object.location.id,
            }
            return JsonResponse(data)
        else:
            return response
