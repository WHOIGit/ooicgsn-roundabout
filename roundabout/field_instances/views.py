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
import requests
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse

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
from rest_framework.views import APIView
from rest_framework.reverse import reverse, reverse_lazy
from .models import *
from .forms import *
from roundabout.inventory.models import Action
from roundabout.inventory.api.serializers import ActionSerializer
from roundabout.locations.api.serializers import LocationSerializer

# Import environment variables from .env files
import environ

env = environ.Env()


# Views to handle syncing requests
# --------------------------------
BASE_URL = env("RDB_SITE_URL")
API_VERSION = "/api/v1"
serializer_mappings = {"location": LocationSerializer, "action": ActionSerializer}
api_url_mappings = {
    "location": f"{BASE_URL}{API_VERSION}/locations/",
    "action": f"{BASE_URL}{API_VERSION}/actions/",
    "photo": f"{BASE_URL}{API_VERSION}/photos/",
}


def field_instance_sync_main(request, field_instance):
    status_code = 401
    pk_mappings = {"location": [], "inventory": [], "build": []}
    api_token = request.GET.get("api_token")

    if not api_token:
        error = "No api_token query paramater data"
        return error

    headers = {
        "Authorization": "Token " + api_token,
    }

    # Get all Actions performed on this FieldInstance
    actions = Action.objects.filter(created_at__gte=field_instance.start_date).order_by(
        "created_at"
    )
    # perform sync operations on each Action based on object_type/action_type
    for action in actions:
        if action.action_type == Action.ADD:
            mappings_data = _sync_new_object(action, pk_mappings, headers, request)
            pk_mappings[mappings_data["object_type"]].append(
                mappings_data["pk_mapping"]
            )
        else:
            status_code = _sync_existing_objects(action, pk_mappings, headers, request)

        # add the Action history object
        mappings_data = _sync_new_object(action, pk_mappings, headers, request, True)
    print(pk_mappings)
    return status_code


def _sync_new_object(action, pk_mappings, headers, request, sync_action=False):
    # check if we're syncing the Action record object or the object_type it references
    if sync_action:
        obj = action
    else:
        field_name = action.object_type
        obj = getattr(action, field_name)

    if obj:
        object_type = obj._meta.model_name
        serializer = serializer_mappings[object_type]

        # serialize data for JSON request
        serializer_results = serializer(obj, context={"request": request})
        data_dict = serializer_results.data

        # Need to remap any Related Fields that may have new PKs
        related_fields_list = ["parent", "location", "build", "inventory"]

        for field in related_fields_list:
            if hasattr(obj, field):
                # reset the mapping dict key to the current object_type if "parent" tree field
                if field == "parent":
                    if sync_action:
                        pk_mapping_key = "inventory"
                    else:
                        pk_mapping_key = object_type
                else:
                    pk_mapping_key = field

                new_key = next(
                    (
                        pk
                        for pk in pk_mappings[pk_mapping_key]
                        if pk["old_pk"] == data_dict[field]
                    ),
                    False,
                )
                if new_key:
                    print(new_key)
                    data_dict[field] = new_key["new_pk"]
        # These will be POST as new item, so remove id
        data_dict.pop("id")
        print(data_dict)
        response = requests.post(
            api_url_mappings[object_type], json=data_dict, headers=headers
        )
        print(f"{object_type} CODE: {response.status_code}")
        print(response.json())
        new_obj = response.json()
        old_pk = data_dict["url"]
        # map the old "local" PK to the new PK saved in the Home Base RDB
        pk_mapping = {"old_pk": old_pk, "new_pk": new_obj["url"]}
        response = {"pk_mapping": pk_mapping, "object_type": object_type}

        # run extra sync request required for specific Models
        if sync_action:
            # Upload any photos for new Action notes
            if obj.photos.exists():
                for photo in obj.photos.all():
                    multipart_form_data = {
                        "photo": (photo.photo.name, photo.photo.file),
                        #'inventory': (None, photo.inventory.id),
                        "action": (None, new_obj["url"]),
                        "user": (None, new_obj["user"]),
                    }
                    response = requests.post(
                        api_url_mappings["photo"],
                        files=multipart_form_data,
                        headers=headers,
                    )
                    print("PHOTO RESPONSE:", response.text)
                    print("PHOTO CODE: ", response.status_code)
    return response


def _sync_existing_objects(action, pk_mappings, headers, request):
    status = None
    field_name = action.object_type
    obj = getattr(action, field_name)

    if obj:
        # serialize data for JSON request
        object_type = obj._meta.model_name
        serializer = serializer_mappings[object_type]
        serializer_results = serializer(obj, context={"request": request})
        data_dict = serializer_results.data
        print(data_dict)
        # Need to remap any Parent items that have new PKs
        new_key = next(
            (
                pk
                for pk in pk_mappings[object_type]
                if pk["old_pk"] == data_dict["parent"]
            ),
            False,
        )
        if new_key:
            print("NEW KEY: " + new_key)
            data_dict["parent"] = new_key["new_pk"]

        url = f"{api_url_mappings[object_type]}{obj.id}/"
        response = requests.patch(url, json=data_dict, headers=headers)
        print(f"{object_type} RESPONSE: {response.text}")
        print(f"{object_type} CODE: {response.status_code}")
        status = response.status_code
    return status


def _sync_request_actions(request, field_instance, obj, inventory_pk_mappings=None):
    action_url = base_url + reverse("api_v1:actions-list")
    photo_url = base_url + reverse("api_v1:photos-list")
    # Get all actions for this object
    object_type = obj._meta.model_name
    actions = obj.actions.filter(object_type=object_type).filter(
        created_at__gte=field_instance.start_date
    )

    for action in actions:
        # serialize data for JSON request
        action_serializer = function_mappings[action]
        action_dict = action_serializer.data
        # These will be POST as new, so remove id
        action_dict.pop("id")
        response = requests.post(action_url, json=action_dict)
        print("ACTION RESPONSE:", response.text)
        print("ACTION CODE: ", response.status_code)
        new_action = response.json()
        # Upload any photos for new Action notes
        if action.photos.exists():
            for photo in action.photos.all():
                multipart_form_data = {
                    "photo": (photo.photo.name, photo.photo.file),
                    #'inventory': (None, photo.inventory.id),
                    "action": (None, new_action["action"]["id"]),
                    "user": (None, photo.user.id),
                }
                response = requests.post(photo_url, files=multipart_form_data)
                print("PHOTO RESPONSE:", response.text)
                print("PHOTO CODE: ", response.status_code)

    return "ACTIONS COMPLETE"


class FieldInstanceSyncToHomeView(APIView):
    def get(self, request, *args, **kwargs):
        # Get the FieldInstance object that is current
        field_instance = FieldInstance.objects.filter(is_this_instance=True).first()
        if not field_instance:
            return HttpResponse("ERROR. This is not a Field Instance of RDB.")

        status_response = field_instance_sync_main(request, field_instance)
        print(status_response)

        if status_response == 200:
            return HttpResponse("Code 200")
        else:
            return HttpResponse(status_response)


# Basic CBVs to handle CRUD operations
# -----------------------------------


class FieldInstanceListView(LoginRequiredMixin, ListView):
    model = FieldInstance
    template_name = "field_instances/field_instance_list.html"
    context_object_name = "field_instances"


class FieldInstanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = FieldInstance
    form_class = FieldInstanceForm
    template_name = "field_instances/field_instance_form.html"
    context_object_name = "field_instance"
    permission_required = "field_instances.add_fieldinstance"
    redirect_field_name = "home"

    def get_success_url(self):
        return reverse(
            "field_instances:field_instances_home",
        )


class FieldInstanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FieldInstance
    form_class = FieldInstanceForm
    template_name = "field_instances/field_instance_form.html"
    context_object_name = "field_instance"
    permission_required = "field_instances.add_fieldinstance"
    redirect_field_name = "home"

    def get_success_url(self):
        return reverse(
            "field_instances:field_instances_home",
        )


class FieldInstanceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = FieldInstance
    success_url = reverse_lazy("field_instances:field_instances_home")
    permission_required = "field_instances.delete_fieldinstance"
    redirect_field_name = "home"
