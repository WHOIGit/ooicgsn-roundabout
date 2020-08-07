import requests
import json
import random
import os

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View
from django.db.models import Q

from .models import FieldInstance
from roundabout.inventory.api.serializers import InventorySerializer, ActionSerializer
from roundabout.inventory.models import Inventory, Action, PhotoNote
from roundabout.parts.models import Part, Revision
from roundabout.locations.models import Location

class FieldInstanceSyncToHomeView(View):

    def get(self, request, *args, **kwargs):
        # Get the FieldInstance object that is current
        field_instance = FieldInstance.objects.filter(is_this_instance=True).first()
        if not field_instance:
            return HttpResponse('ERROR. This is not a Field Instance of RDB.')
        user_list = field_instance.users
        #actions = Action.objects.filter(user__in=user_list.all()).filter(created_at__gte=field_instance.start_date)
        # need a data structure to hold mappings of field instance ID to new home base ID
        pk_mappings = []

        ##### SYNC INVENTORY #####
        #base_url = 'https://ooi-cgrdb-staging.whoi.net'
        base_url = 'https://ooi-cgrdb-staging.whoi.net'
        inventory_url = F"{base_url}/api/v1/inventory/"
        action_url = F"{base_url}/api/v1/actions/"
        action_url = F"{base_url}/api/v1/photos/"
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
                context={'request': request, }
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
        #actions_other_qs = actions.filter(object_type=Action.INVENTORY).exclude(action_type=Action.ADD).order_by('inventory', '-parent')
        if existing_inventory:
            #existing_inventory = [action.inventory for action in actions_other_qs.exclude(inventory__in=new_inventory).distinct('inventory')]
            print(existing_inventory)

            inventory_serializer = InventorySerializer(
                existing_inventory,
                many=True,
                context={'request': request, }
            )
            inventory_dict = inventory_serializer.data

            for item in inventory_dict:
                print(json.dumps(item))
                url = F"{inventory_url}{item['id']}/"
                print(url)

                # Need to remap any Parent items that have new PKs
                new_key = next((pk for pk in pk_mappings if pk['old_pk'] == item['parent']), False)
                if new_key:
                    print('NEW KEY: ', new_key)
                    item['parent'] = new_key['new_pk']

                response = requests.patch(url, json=item, )
                print(response.status_code)

            # post all new Actions for this item
            for inv in existing_inventory:
                actions = inv.actions.filter(created_at__gte=field_instance.start_date)
                print(actions)
                actions_serializer = ActionSerializer(
                    actions,
                    many=True,
                    context={'request': request, }
                )
                actions_dict = actions_serializer.data
                print(actions_dict)
                for action in actions_dict:
                    action.pop('id')
                    photos = action.pop('photos')
                    print('PHOTOS ', photos)
                    response = requests.post(action_url, json=action,)
                    print(json.dumps(action))
                    print('ACTION RESPONSE:', response.text)
                    new_action = response.text
                    print("Action Post: ", response.status_code)
                    # Add the photos for Action notes if they exist
                    if photos:
                        photo_qs = PhotoNote.objects.filter(id__in=photos)
                        for photo in photo_qs:
                            multipart_form_data = {
                                'photo': (photo.photo.name, photo.photo.file),
                                #'photo': (photo.photo.name, open('myfile.zip', 'rb')),
                                'inventory': (None, photo.inventory.id),
                                'action': (None, new_action['id']),
                                'user': (None, photo.user.id)
                            }
                            response = requests.post(photo_url, files=multipart_form_data, )
                            print("Photo post: ", response.status_code)

        if response:
            return HttpResponse("Code 200")
        else:
            return HttpResponse("API error")
