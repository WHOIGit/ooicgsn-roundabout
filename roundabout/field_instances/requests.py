import requests
import json
import random
import os

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View
from django.db.models import Q

#from .models import FieldInstance
from .models import *
from roundabout.inventory.api.serializers import InventorySerializer, ActionSerializer
from roundabout.inventory.models import Inventory, Action, PhotoNote
from roundabout.parts.models import Part, Revision
from roundabout.locations.models import Location

"""
Request function to sync Field Instance: Inventory items
Args - field_instance: FieldInstance object
"""
def sync_request_inventory(field_instance):
    pk_mappings = []

    ##### SYNC INVENTORY #####
    #base_url = 'https://ooi-cgrdb-staging.whoi.net'
    base_url = 'https://ooi-cgrdb-staging.whoi.net'
    inventory_url = F"{base_url}/api/v1/inventory/"
    action_url = F"{base_url}/api/v1/actions/"
    photo_url = F"{base_url}/api/v1/photos/"
    # Get new items that were added, these need special handling
    new_inventory = Inventory.objects.filter(created_at__gte=field_instance.start_date).order_by('-parent')
    #actions_add_qs = actions.filter(object_type=Action.INVENTORY).filter(action_type=Action.ADD).order_by('-parent')
    if new_inventory:
        #new_inventory = [action.inventory for action in actions_add_qs.all()]
        print(new_inventory)
        for item in new_inventory:
            # check if serial number already exists
            response = requests.get(inventory_url, params={'serial_number': item.serial_number}, headers={'Content-Type': 'application/json'}, )
            if response.json():
                # Need to change the Serial Number to avoid naming conflict
                item.serial_number = item.serial_number + '-' + str(random.randint(1,1001))
                #item.save()

        inventory_serializer = InventorySerializer(
            new_inventory,
            many=True,
            #context={'request': request, }
        )
        inventory_dict = inventory_serializer.data

        for item in inventory_dict:
            old_pk = item['id']
            item.pop('id')
            # Need to remap any Parent items that have new PKs
            new_key = next((pk for pk in pk_mappings if pk['old_pk'] == item['parent']), False)
            if new_key:
                print('NEW KEY: ' + new_key)
                item['parent'] = new_key['new_pk']

            print(json.dumps(item))
            """
            response = requests.post(inventory_url, data=json.dumps(item), headers={'Content-Type': 'application/json'}, )
            print('RESPONSE:', response.json())
            new_obj = response.json()
            pk_mappings.append({'old_pk': old_pk, 'new_pk': new_obj['id']})
            """
        print(pk_mappings)

    # Get all existing items in Home Base RDB
    existing_inventory = Inventory.objects.filter(
        Q(updated_at__gte=field_instance.start_date) & Q(created_at__lt=field_instance.start_date)
    )
    if existing_inventory:
        print(existing_inventory)
        for inv in existing_inventory:
            # serialize data for JSON request
            inventory_serializer = InventorySerializer(inv)
            inventory_dict = inventory_serializer.data
            url = F"{inventory_url}{inv.id}/"
            print(url)
            # Need to remap any Parent items that have new PKs
            new_key = next((pk for pk in pk_mappings if pk['old_pk'] == inventory_dict['parent']), False)
            if new_key:
                print('NEW KEY: ', new_key)
                inventory_dict['parent'] = new_key['new_pk']

            response = requests.patch(url, json=inventory_dict, )
            print('INVENTORY RESPONSE:', response.text)
            print("INVENTORY CODE: ", response.status_code)

            # post all new Actions for this item
            actions = inv.actions.filter(created_at__gte=field_instance.start_date)
            for action in actions:
                # serialize data for JSON request
                action_serializer = ActionSerializer(action)
                action_dict = action_serializer.data
                # These will be POST as new, so remove id
                action_dict.pop('id')
                response = requests.post(action_url, json=action_dict )
                print('ACTION RESPONSE:', response.text)
                print("ACTION CODE: ", response.status_code)
                new_action = response.json()
                # Upload any photos for new Action notes
                if action.photos.exists():
                    for photo in action.photos.all():
                        multipart_form_data = {
                            'photo': (photo.photo.name, photo.photo.file),
                            #'photo': (photo.photo.name, open('myfile.zip', 'rb')),
                            'inventory': (None, photo.inventory.id),
                            'action': (None, new_action['action']['id']),
                            'user': (None, photo.user.id)
                        }
                        response = requests.post(photo_url, files=multipart_form_data )
                        print('PHOTO RESPONSE:', response.text)
                        print("PHOTO CODE: ", response.status_code)

        return response.status_code
