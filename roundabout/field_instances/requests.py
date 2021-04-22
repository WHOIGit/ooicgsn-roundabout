import requests
import json
import random
import os

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View
from django.db.models import Q
from django.contrib.sites.shortcuts import get_current_site
from rest_framework.reverse import reverse, reverse_lazy

# from .models import FieldInstance
from .models import *
from roundabout.inventory.api.serializers import InventorySerializer, ActionSerializer
from roundabout.inventory.models import Inventory, Action, PhotoNote
from roundabout.userdefinedfields.api.serializers import (
    FieldSerializer,
    FieldValueSerializer,
)
from roundabout.userdefinedfields.models import Field
from roundabout.parts.models import Part, Revision
from roundabout.locations.models import Location
from roundabout.locations.api.serializers import LocationSerializer


# Import environment variables from .env files
import environ

env = environ.Env()
base_url = env("RDB_SITE_URL")
api_version_url = "/api/v1"
"""
Main sync function to coordinate the different models
"""


def field_instance_sync_main(request, field_instance):
    status_code = 401
    pk_mappings = []
    # Sync base models needed for DB relationships
    # Run Location sync
    location_pk_mappings = _sync_request_locations(request, field_instance)
    print(location_pk_mappings)
    pk_mappings.update({"location_pk_mappings": location_pk_mappings})
    # Run Field model sync
    field_pk_mappings = _sync_request_fields(request, field_instance)
    pk_mappings.update({"field_pk_mappings": field_pk_mappings})
    # Sync Inventory items
    inventory_respone = _sync_request_inventory(request, field_instance, pk_mappings)
    status_code = inventory_respone
    print("STATUS CODE: ", inventory_respone)
    return status_code


"""
Function to sync NEW objects
"""


def _sync_new_objects(field_instance, model, api_url, serializer):
    pk_mappings = []
    new_objects = model.objects.filter(created_at__gte=field_instance.start_date)

    if new_objects:
        for obj in new_objects:
            old_pk = obj.id
            # serialize data for JSON request
            serializer = serializer(obj)
            data_dict = serializer.data
            # Need to remap any Parent items that have new PKs
            new_key = next(
                (pk for pk in pk_mappings if pk["old_pk"] == data_dict["parent"]), False
            )
            if new_key:
                print("NEW KEY: " + new_key)
                data_dict["parent"] = new_key["new_pk"]
            # These will be POST as new item, so remove id
            data_dict.pop("id")
            response = requests.post(api_url, json=data_dict)
            print(f"{model._meta.model_name} RESPONSE: {response.text}")
            print(f"{model._meta.model_name} CODE: {response.status_code}")
            new_obj = response.json()[model._meta.model_name]
            pk_mappings.append({"old_pk": old_pk, "new_pk": new_obj["id"]})
    return pk_mappings


"""
Function to sync EXISTING objects
"""


def _sync_existing_objects(field_instance, model, api_url, serializer, pk_mappings):
    status = None
    # Get all existing fields in Home Base RDB that were updated
    existing_objects = model.objects.filter(
        Q(updated_at__gte=field_instance.start_date)
        & Q(created_at__lt=field_instance.start_date)
    )
    if existing_objects:
        for obj in existing_objects:
            # serialize data for JSON request
            serializer = serializer(obj)
            data_dict = serializer.data
            # Need to remap any Parent items that have new PKs
            new_key = next(
                (pk for pk in pk_mappings if pk["old_pk"] == data_dict["parent"]), False
            )
            if new_key:
                print("NEW KEY: " + new_key)
                data_dict["parent"] = new_key["new_pk"]

            url = f"{api_url}{obj.id}/"
            response = requests.patch(
                url,
                json=data_dict,
            )
            print(f"{model._meta.model_name} RESPONSE: {response.text}")
            print(f"{model._meta.model_name} CODE: {response.status_code}")
            status = response.status_code
    return status


"""
Request function to sync Field Instance: Locations
Args:
request: Django request object
field_values: queryset of FieldValue objects
Returns:
location_pk_mappings: array that maps old_pk to new_pk for new objects
"""


def _sync_request_locations(request, field_instance):
    model = Location
    serializer = LocationSerializer
    api_url = base_url + reverse("locations-list")
    # Sync new objects, return the pk_mappings for new items
    pk_mappings = _sync_new_objects(field_instance, model, api_url, serializer)
    status = _sync_existing_objects(
        field_instance, model, api_url, serializer, pk_mappings
    )

    return pk_mappings


"""
Request function to sync Field Instance: Fields
Args:
request: Django request object
field_values: queryset of FieldValue objects
pk_mappings: array that maps old_pk to new_pk for new objects
"""


def _sync_request_fields(request, field_instance):
    model = Field
    serializer = FieldSerializer
    api_url = base_url + reverse("api_v1:userdefined-fields/fields-list")
    # Sync new objects, return the pk_mappings for new items
    pk_mappings = _sync_new_objects(field_instance, model, api_url, serializer)
    status = _sync_existing_objects(
        field_instance, model, api_url, serializer, pk_mappings
    )

    """
    field_url = base_url + reverse('userdefinedfields/fields-list')
    field_pk_mappings = []
    # Get new fields that were added
    new_fields = Field.objects.filter(created_at__gte=field_instance.start_date)
    if new_fields:
        for field in new_fields:
            old_pk = field['id']
            # serialize data for JSON request
            field_serializer = FieldSerializer(field)
            field_dict = field_serializer.data
            # These will be POST as new, so remove id
            field_dict.pop('id')
            response = requests.post(field_url, json=field_dict )
            print('Field RESPONSE:', response.text)
            print("Field CODE: ", response.status_code)
            new_obj = response.json()
            field_pk_mappings.append({'old_pk': old_pk, 'new_pk': new_obj['id']})

    # Get all existing fields in Home Base RDB that were updated
    existing_fields = Field.objects.filter(
        Q(updated_at__gte=field_instance.start_date) & Q(created_at__lt=field_instance.start_date)
    )
    if existing_fields:
        for field in existing_fields:
            # serialize data for JSON request
            field_serializer = FieldSerializer(field)
            field_dict = field_serializer.data
            url = base_url + reverse('userdefinedfields/fields-detail', kwargs={'pk': field.id},)
            response = requests.patch(url, json=field_dict, )
            print('Field RESPONSE:', response.text)
            print("Field CODE: ", response.status_code)
    """
    return pk_mappings


"""
Request function to sync Field Instance: Inventory items
Args:
request: Django request object
field_instance: FieldInstance object
"""


def _sync_request_inventory(request, field_instance, pk_mappings):
    inventory_pk_mappings = []

    ##### SYNC INVENTORY #####
    # inventory_url = F"{base_url}/api/v1/inventory/"
    inventory_url = base_url + reverse("api_v1:inventory-list")
    print(inventory_url)
    # Get new items that were added, these need special handling
    new_inventory = Inventory.objects.filter(
        created_at__gte=field_instance.start_date
    ).order_by("-parent")
    # actions_add_qs = actions.filter(object_type=Action.INVENTORY).filter(action_type=Action.ADD).order_by('-parent')
    if new_inventory:
        # new_inventory = [action.inventory for action in actions_add_qs.all()]
        print(new_inventory)
        for item in new_inventory:
            # check if serial number already exists
            response = requests.get(
                inventory_url,
                params={"filter{serial_number}": item.serial_number},
                headers={"Content-Type": "application/json"},
            )
            if response.json():
                # Need to change the Serial Number to avoid naming conflict
                item.serial_number = (
                    item.serial_number + "-" + str(random.randint(1, 1001))
                )
                # item.save()

        inventory_serializer = InventorySerializer(
            new_inventory,
            many=True,
            # context={'request': request, }
        )
        inventory_dict = inventory_serializer.data

        for item in inventory_dict:
            old_pk = item["id"]
            item.pop("id")
            # Need to remap any Parent items that have new PKs
            new_key = next(
                (pk for pk in inventory_pk_mappings if pk["old_pk"] == item["parent"]),
                False,
            )
            if new_key:
                print("NEW KEY: " + new_key)
                item["parent"] = new_key["new_pk"]

            print(json.dumps(item))
            """
            response = requests.post(inventory_url, data=json.dumps(item), headers={'Content-Type': 'application/json'}, )
            print('RESPONSE:', response.json())
            new_obj = response.json()
            inventory_pk_mappings.append({'old_pk': old_pk, 'new_pk': new_obj['id']})
            """
        print(inventory_pk_mappings)

    # Get all existing items in Home Base RDB
    existing_inventory = Inventory.objects.filter(
        Q(updated_at__gte=field_instance.start_date)
        & Q(created_at__lt=field_instance.start_date)
    )
    if existing_inventory:
        print(existing_inventory)
        for inv in existing_inventory:
            # serialize data for JSON request
            inventory_serializer = InventorySerializer(inv)
            inventory_dict = inventory_serializer.data
            url = base_url + reverse(
                "api_v1:inventory-detail",
                kwargs={"pk": inv.id},
            )
            # url = F"{inventory_url}{inv.id}/"
            print(url)
            # Need to remap any Parent items that have new PKs
            new_key = next(
                (
                    pk
                    for pk in inventory_pk_mappings
                    if pk["old_pk"] == inventory_dict["parent"]
                ),
                False,
            )
            if new_key:
                print("NEW KEY: ", new_key)
                inventory_dict["parent"] = new_key["new_pk"]

            response = requests.patch(
                url,
                json=inventory_dict,
            )
            print("INVENTORY RESPONSE:", response.text)
            print("INVENTORY CODE: ", response.status_code)

            # post all new Actions for this item
            action_response = _sync_request_actions(
                request, field_instance, inv, inventory_pk_mappings
            )
            # post all Field Values for this item
            field_value_response = _sync_request_field_values(
                request, field_instance, inv, field_pk_mappings, inventory_pk_mappings
            )

        return response.status_code


"""
Request function to sync Field Instance: Actions
Args:
request: Django request object
actions: queryset of Action objects
pk_mappings: array that maps old_pk to new_pk for new objects
"""


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
        action_serializer = ActionSerializer(action)
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


"""
Request function to sync Field Instance: FieldValues
Args:
request: Django request object
field_instance: FieldInstance object
inventory_item: Inventory object
field_pk_mappings, inventory_pk_mappings: array that maps old_pk to new_pk for new objects
"""


def _sync_request_field_values(
    request,
    field_instance,
    inventory_item,
    field_pk_mappings,
    inventory_pk_mappings=None,
):
    field_value_url = base_url + reverse("api_v1:userdefined-fields/field-values-list")
    # Get new field values that were added
    new_field_values = inventory_item.fieldvalues.filter(
        created_at__gte=field_instance.start_date
    )
    for fv in new_field_values:
        # serialize data for JSON request
        fv_serializer = FieldValueSerializer(fv)
        fv_dict = fv_serializer.data
        # These will be POST as new, so remove id
        fv_dict.pop("id")
        response = requests.post(field_value_url, json=fv_dict)
        print("Field Value RESPONSE:", response.text)
        print("Field Value CODE: ", response.status_code)

    # Get all existing field values in Home Base RDB that were updated
    existing_field_values = inventory_item.fieldvalues.filter(
        Q(updated_at__gte=field_instance.start_date)
        & Q(created_at__lt=field_instance.start_date)
    )
    for fv in existing_field_values:
        # serialize data for JSON request
        fv_serializer = FieldValueSerializer(fv)
        fv_dict = fv_serializer.data
        url = base_url + reverse(
            "api_v1:userdefinedfields/field-values-detail",
            kwargs={"pk": fv.id},
        )
        response = requests.post(field_value_url, json=fv_dict)
        print("Field Value RESPONSE:", response.text)
        print("Field Value CODE: ", response.status_code)

    return "FIELD VALUES COMPLETE"
