import requests
import json

from django.http import HttpResponse
from django.views.generic import View

from .models import FieldInstance
from roundabout.inventory.api.serializers import InventorySerializer
from roundabout.inventory.models import Inventory, Action
from roundabout.parts.models import Part, Revision
from roundabout.locations.models import Location

class FieldInstanceSyncToHomeView(View):

    def get(self, request, *args, **kwargs):
        # Get the FieldInstance object that is current
        field_instance = FieldInstance.objects.filter(is_this_instance=True).last()
        if not field_instance:
            return HttpResponse('ERROR. This is not a Field Instance of RDB.')
        user_list = field_instance.users
        actions = Action.objects.filter(user__in=user_list.all()).filter(created_at__gte=field_instance.start_date)
        # need a data structure to hold mappings of field instance ID to new home base ID
        pk_mappings = []

        ##### SYNC INVENTORY #####
        base_url = 'http://localhost:8000/api/v1/inventory/'
        # Get new items that were added, these need special handling
        actions_add_qs = actions.filter(object_type=Action.INVENTORY).filter(action_type=Action.ADD)
        if actions_add_qs:
            new_inventory = [action.inventory for action in actions_add_qs.all()]
            print(new_inventory)
            for item in new_inventory:
                # check if serial number already exists
                response = requests.get(base_url, params={'serial_number': item.serial_number}, headers={'Content-Type': 'application/json'}, )
                if response.json():
                    # Need to change the Serial Number to avoid naming conflict
                    item.serial_number = item.serial_number + '-Z'
                    item.save()

            inventory_serializer = InventorySerializer(
                new_inventory,
                many=True,
                context={'request': request, }
            )
            inventory_dict = inventory_serializer.data

            for item in inventory_dict:
                old_pk = item['id']
                item.pop('id')
                # testing
                item['serial_number'] = '999-9999-Zc'
                print(json.dumps(item))
                url = base_url
                response = requests.post(url, data=json.dumps(item), headers={'Content-Type': 'application/json'}, )
                print(response.json())
                new_obj = response.json()
                pk_mappings.append({'old_pk': old_pk, 'new_pk': new_obj['id']})
            print(pk_mappings)

        # Get all existing items in Home Base RDB
        actions_other_qs = actions.filter(object_type=Action.INVENTORY).exclude(action_type=Action.ADD)
        if actions_other_qs:
            existing_inventory = [action.inventory for action in actions_other_qs.all()]
            print(existing_inventory)

            inventory_serializer = InventorySerializer(
                existing_inventory,
                many=True,
                context={'request': request, }
            )
            inventory_dict = inventory_serializer.data

            for item in inventory_dict:
                print(json.dumps(item))
                url = F"{base_url}{item['id']}/"
                print(url)
                response = requests.patch(url, data=json.dumps(item), headers={'Content-Type': 'application/json'}, )
                print(response.status_code)
            #response = requests.post(url, auth=HTTPBasicAuth('USER', 'PASSWORD'), headers={'Content-Type': 'application/json'}, json=body)

        if response.status_code == 200:
            return HttpResponse("Code 200")
        else:
            return HttpResponse("API error")
