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

from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import (
    View,
    DetailView,
    ListView,
    RedirectView,
    UpdateView,
    CreateView,
    DeleteView,
    TemplateView,
    FormView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from common.util.mixins import AjaxFormMixin
from .models import Build, BuildAction
from .forms import *
from roundabout.locations.models import Location
from roundabout.inventory.models import (
    Inventory,
    Action,
    Deployment,
    DeploymentAction,
    InventoryDeployment,
)
from roundabout.inventory.utils import _create_action_history
from roundabout.calibrations.utils import handle_reviewers

# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels

labels = set_app_labels()

## CBV views for Deployments as part of Builds app ##

# Create Deployment for Build
class DeploymentAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Deployment
    form_class = DeploymentStartForm
    context_object_name = "deployment"
    template_name = "builds/ajax_deployment_form.html"

    def get_context_data(self, **kwargs):
        context = super(DeploymentAjaxCreateView, self).get_context_data(**kwargs)
        if "build_pk" in self.kwargs:
            build = Build.objects.get(id=self.kwargs["build_pk"])
        # Add Build to the context to validate date options
        context.update({"build": build})
        return context

    def get_initial(self):
        # Returns the initial data to use for forms on this view.
        initial = super(DeploymentAjaxCreateView, self).get_initial()
        if "build_pk" in self.kwargs:
            build = Build.objects.get(id=self.kwargs["build_pk"])
            initial["build"] = build
            initial["location"] = build.location
        return initial

    def get_success_url(self):
        return reverse("builds:ajax_builds_detail", args=(self.object.build.id,))

    def form_valid(self, form):
        action_type = Action.STARTDEPLOYMENT
        action_date = form.cleaned_data["date"]
        self.object = form.save()
        self.object.deployment_start_date = action_date
        self.object.save()

        # Update the Build instance to match any Deployment changes
        build = self.object.build
        build.location = self.object.location
        build.is_deployed = True
        build.save()
        # Create Build Action record for deployment
        _create_action_history(build, action_type, self.request.user)

        # Get all Inventory items on Build, match location and add Action
        inventory_items = build.inventory.all()
        for item in inventory_items:
            item.location = build.location
            item.save()
            # Call the function to create an Action history chain for this event
            _create_action_history(item, action_type, self.request.user, build)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.build.id,
                "object_type": "builds",
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response


class DeploymentAjaxUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = Deployment
    form_class = DeploymentForm
    context_object_name = "deployment"
    template_name = "builds/ajax_deployment_form.html"

    def get_context_data(self, **kwargs):
        context = super(DeploymentAjaxUpdateView, self).get_context_data(**kwargs)

        if "action_type" in self.kwargs:
            context["action_type"] = self.kwargs["action_type"]
        else:
            context["action_type"] = None

        return context

    # Custom class method to update action histories on Deployment updates
    def _update_actions(self, obj_to_update=None, action_to_update=None):
        obj_to_copy = self.object
        actions_list = [
            Action.STARTDEPLOYMENT,
            Action.DEPLOYMENTBURNIN,
            Action.DEPLOYMENTTOFIELD,
            Action.DEPLOYMENTRECOVER,
            Action.DEPLOYMENTRETIRE,
        ]

        if not obj_to_update:
            obj_to_update = self.object

        if action_to_update:
            actions_list = []
            actions_list = [action_to_update]

        actions = obj_to_update.get_actions()
        actions = actions.filter(action_type__in=actions_list)

        for action in actions:
            if (
                action.action_type == Action.STARTDEPLOYMENT
                and obj_to_copy.deployment_start_date
            ):
                action.created_at = obj_to_copy.deployment_start_date

            if (
                action.action_type == Action.DEPLOYMENTBURNIN
                and obj_to_copy.deployment_burnin_date
            ):
                action.created_at = obj_to_copy.deployment_burnin_date

            if (
                action.action_type == Action.DEPLOYMENTTOFIELD
                and obj_to_copy.deployment_to_field_date
            ):
                action.created_at = obj_to_copy.deployment_to_field_date

            if (
                action.action_type == Action.DEPLOYMENTRECOVER
                and obj_to_copy.deployment_recovery_date
            ):
                action.created_at = obj_to_copy.deployment_recovery_date

            if (
                action.action_type == Action.DEPLOYMENTRETIRE
                and obj_to_copy.deployment_retire_date
            ):
                action.created_at = obj_to_copy.deployment_retire_date
            action.save()

        return actions

    def form_valid(self, form):
        action_type = Action.DEPLOYMENTDETAILS
        previous_deployment = Deployment.objects.get(id=self.object.pk)
        form.instance.approved = False
        form.save()
        handle_reviewers(form)
        self.object = form.save()
        self.object.build.detail = "%s Details changed." % (
            self.object.deployment_number
        )
        self.object.build.save()
        # Create Build Action record for deployment
        build_record = _create_action_history(
            self.object.build,
            action_type,
            self.request.user,
        )

        # can only associate one cruise with an action, so for deployment detail change, only show changed cruise value
        cruise_deployed_change = (
            previous_deployment.cruise_deployed != self.object.cruise_deployed
        )
        cruise_recovered_change = (
            previous_deployment.cruise_recovered != self.object.cruise_recovered
        )
        if cruise_deployed_change and cruise_recovered_change:
            pass  # can't record both so record neither
        elif cruise_deployed_change:
            build_record.cruise = self.object.cruise_deployed
        elif cruise_recovered_change:
            build_record.cruise = self.object.cruise_recovered
        build_record.save()

        # Update Deployment Action items to match any date changes
        self._update_actions(self.object)

        # Check all Inventory deployments associated with this Deployment
        # If deployment_to_field_date OR deployment_recovery_date matches the Build Deployment,
        # need to update those Inventory Deployments
        inventory_deployments = self.object.inventory_deployments.all()

        for inventory_deployment in inventory_deployments:
            if inventory_deployment.deployment_start_date.replace(
                second=0, microsecond=0
            ) == previous_deployment.deployment_start_date.replace(
                second=0, microsecond=0
            ):
                inventory_deployment.deployment_start_date = (
                    self.object.deployment_start_date
                )
                # Update Deployment Action items to match any date changes
                self._update_actions(inventory_deployment, Action.STARTDEPLOYMENT)

            if (
                inventory_deployment.deployment_burnin_date
                == previous_deployment.deployment_burnin_date
            ):
                inventory_deployment.deployment_burnin_date = (
                    self.object.deployment_burnin_date
                )
                # Update Deployment Action items to match any date changes
                self._update_actions(inventory_deployment, Action.DEPLOYMENTBURNIN)

            if (
                inventory_deployment.deployment_to_field_date
                == previous_deployment.deployment_to_field_date
            ):
                inventory_deployment.deployment_to_field_date = (
                    self.object.deployment_to_field_date
                )
                # Update Deployment Action items to match any date changes
                self._update_actions(inventory_deployment, Action.DEPLOYMENTTOFIELD)

            if (
                inventory_deployment.deployment_recovery_date
                == previous_deployment.deployment_recovery_date
            ):
                inventory_deployment.deployment_recovery_date = (
                    self.object.deployment_recovery_date
                )
                # Update Deployment Action items to match any date changes
                self._update_actions(inventory_deployment, Action.DEPLOYMENTRECOVER)

            if (
                inventory_deployment.deployment_retire_date
                == previous_deployment.deployment_retire_date
            ):
                inventory_deployment.deployment_retire_date = (
                    self.object.deployment_retire_date
                )
                # Update Deployment Action items to match any date changes
                self._update_actions(inventory_deployment, Action.DEPLOYMENTRETIRE)

            inventory_deployment.save()

        if self.request.is_ajax():
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.build.id,
                "object_type": self.object.build.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("builds:ajax_builds_detail", args=(self.object.build.id,))


class DeploymentAjaxActionView(DeploymentAjaxUpdateView):
    def get_context_data(self, **kwargs):
        context = super(DeploymentAjaxActionView, self).get_context_data(**kwargs)
        latest_action_record = (
            self.object.build.get_actions().filter(deployment=self.object).first()
        )

        context.update({"latest_action_record": latest_action_record})
        return context

    def get_form_class(self):
        ACTION_FORMS = {
            "deploymentburnin": DeploymentActionBurninForm,
            "deploymenttofield": DeploymentActionDeployForm,
            "deploymentrecover": DeploymentActionRecoverForm,
            "deploymentretire": DeploymentActionRetireForm,
            "deploymentdetails": DeploymentActionDetailsForm,
        }
        action_type = self.kwargs["action_type"]
        form_class_name = ACTION_FORMS[action_type]

        return form_class_name

    def form_valid(self, form):
        self.object = form.save()
        action_type = self.kwargs["action_type"]
        action_date = form.cleaned_data["date"]
        # Set Detail and action_type variables
        if action_type == Action.DEPLOYMENTBURNIN:
            self.object.detail = "%s Burn In initiated at %s. " % (
                self.object.deployment_number,
                self.object.location,
            )
            self.object.deployment_burnin_date = action_date
        if action_type == Action.DEPLOYMENTTOFIELD:
            self.object.detail = "%s Deployed to Field: %s. " % (
                self.object.deployment_number,
                self.object.location,
            )
            self.object.deployment_to_field_date = action_date
            self.object.deployed_location = self.object.location
        if action_type == Action.DEPLOYMENTRECOVER:
            self.object.detail = "%s Recovered to: %s. " % (
                self.object.deployment_number,
                self.object.location,
            )
            self.object.deployment_recovery_date = action_date
        if action_type == Action.DEPLOYMENTRETIRE:
            self.object.detail = "%s Ended." % (self.object.deployment_number)
            self.object.deployment_retire_date = action_date
        self.object.save()

        # Update Build location, create Action Record
        build = self.object.build
        build.detail = self.object.detail

        # If action_type is not "retire", update Build location
        if action_type != "deploymentretire":
            build.location = self.object.location

        # If action_type is "retire", update Build deployment status
        if action_type == "deploymentretire":
            build.is_deployed = False

        build.save()
        # Create Build Action record for deployment
        build_record = _create_action_history(
            build, action_type, self.request.user, None, "", action_date
        )
        build_record.cruise = (
            self.object.cruise_recovered or self.object.cruise_deployed
        )
        build_record.save()

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

        detail = build_record.get_action_type_display()
        cruise = None
        deployment_type = 'build_deployment'

        if action_type ==  Action.DEPLOYMENTTOFIELD:
            cruise = self.object.cruise_deployed
        elif action_type ==  Action.DEPLOYMENTRECOVER:
            cruise = self.object.cruise_recovered
        """

        # Get all Inventory items on Build, match location and add Actions
        inventory_items = build.inventory.all()

        for item in inventory_items:
            item.location = build.location
            item.save()
            _create_action_history(
                item, action_type, self.request.user, build, "", action_date
            )

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                "message": "Successfully submitted form data.",
                "object_id": build.id,
                "location_id": self.object.location.id,
                "object_type": "builds",
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response
