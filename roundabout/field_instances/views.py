from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View

from .requests import *

class FieldInstanceSyncToHomeView(View):

    def get(self, request, *args, **kwargs):
        # Get the FieldInstance object that is current
        field_instance = FieldInstance.objects.filter(is_this_instance=True).first()
        if not field_instance:
            return HttpResponse('ERROR. This is not a Field Instance of RDB.')
        user_list = field_instance.users

        status_code = sync_request_inventory(field_instance)
        print(status_code)
        
        if status_code == 200:
            return HttpResponse("Code 200")
        else:
            return HttpResponse("API error")
