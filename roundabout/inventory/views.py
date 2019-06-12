import json
import socket
import os
import xml.etree.ElementTree as ET

from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from itertools import chain

from .models import Inventory, Deployment, Action, DeploymentAction, InventorySnapshot, DeploymentSnapshot
from .forms import *
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision
from roundabout.moorings.models import MooringPart
from roundabout.admintools.models import Printer
from roundabout.userdefinedfields.models import FieldValue, Field
from common.util.mixins import AjaxFormMixin

# Mixins
# ------------------------------------------------------------------------------

class InventoryNavTreeMixin(LoginRequiredMixin, object):

    def get_context_data(self, **kwargs):
        context = super(InventoryNavTreeMixin, self).get_context_data(**kwargs)
        context.update({
            'locations': Location.objects.prefetch_related('deployment__final_location__mooring_parts__part__part_type')
                        .prefetch_related('inventory__part__part_type').prefetch_related('deployment__inventory')
        })
        if 'current_location' in self.kwargs:
            context['current_location'] = self.kwargs['current_location']
        else:
            context['current_location'] = 2

        return context


# General Functions for Inventory
# ------------------------------------------------------------------------------

def load_inventory_navtree(request):
    locations = Location.objects.exclude(root_type='Retired').prefetch_related('deployment__final_location__mooring_parts__part__part_type').prefetch_related('inventory__part__part_type').prefetch_related('deployment__inventory')
    return render(request, 'inventory/ajax_inventory_navtree.html', {'locations': locations})


def make_tree_copy(root_part, new_location, deployment_snapshot, parent=None ):
    # Makes a copy of the tree starting at "root_part", move to new Location, reparenting it to "parent"
    if root_part.part.friendly_name:
        part_name = root_part.part.friendly_name
    else:
        part_name = root_part.part.name

    new_item = InventorySnapshot.objects.create(location=new_location, inventory=root_part, parent=parent, deployment=deployment_snapshot, order=part_name)

    for child in root_part.get_children():
        make_tree_copy(child, new_location, deployment_snapshot, new_item)


# Function to print to network printer via sockets
def print_code_zebraprinter(request, **kwargs):
    code_format = kwargs.get('code_format', 'QR')
    printer_name = request.GET.get('printer_name')
    printer_type = request.GET.get('printer_type')
    serial_number = request.GET.get('serial_number')

    if printer_name and printer_type:
    #try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((printer_name, 9100))

        if printer_type == 'Brady':
            # Need to load XML file so we'll set the path
            module_dir = os.path.dirname(__file__)  # get current directory
            # Set XML Namespace to get clean output
            ET.register_namespace('', "http://www.bradycorp.com/printers/bpl")

            if code_format == 'QR':
                file_path = os.path.join(module_dir, 'printer_template_files/brady-qr.xml')
                tree = ET.parse(file_path)
                root = tree.getroot()

                # modifying the Static Text 'value' attribute to be Serial Number
                for static_text in root.iter('{http://www.bradycorp.com/printers/bpl}static-text'):
                    static_text.set('value', serial_number)

                content = ET.tostring(root, encoding='utf8').decode('utf8')

            elif code_format == 'bar93':
                file_path = os.path.join(module_dir, 'printer_template_files/brady-bar93.xml')
                tree = ET.parse(file_path)
                root = tree.getroot()

                # modifying the Static Text 'value' attribute to be Serial Number
                for static_text in root.iter('{http://www.bradycorp.com/printers/bpl}static-text'):
                    static_text.set('value', serial_number)

                content = ET.tostring(root, encoding='utf8').decode('utf8')

        elif printer_type == 'Zebra':
            if code_format == 'QR':
                content =   '^XA \
                            ^PW400 \
                            ^FO20,20 \
                            ^BQ,2,5 \
                            ^FDMM,A{}^FS \
                            ^FO20,170 \
                            ^A0,30,25 \
                            ^FD{}^FS^XZ'.format(serial_number, serial_number)
                #content = '^XA^PW400^LL200^FO20,20^A0N,30,30~SD25^FDHello Connor^FS^XZ'
            elif code_format == 'bar93':
                content =   '^XA \
                            ^PW400 \
                            ^FO20,20^BY1 \
                            ^BAN,150,Y,N,N \
                            ^FD{}^FS^XZ'.format(serial_number)

        content = content.encode()

        s.sendall(content)
        s.close()

        success = True
        message = 'Label printed.'
        """
        except:
        success = False
        message = 'Printing failed. Check printer status.'
        """
    else:
        success = False
        message = 'Printing failed. Check printer status.'

    data = {
        'message': message,
        'success': success,
    }
    return JsonResponse(data)


# AJAX Functions for Forms
# ------------------------------------------------------------------------------

# Function to load available Parent Inventory items based on Part Template
def load_parents(request):
    part_id = request.GET.get('part')
    location_id = request.GET.get('location')

    if part_id:
        mooring_parts = MooringPart.objects.filter(part_id=part_id)
    else:
        mooring_parts = None

    if mooring_parts and location_id and part_id:
        mooring_parts_list = []
        for mp in mooring_parts:
            if mp.parent:
                mooring_parts_list.append(mp.parent.part.id)
                inventory_list = Inventory.objects.filter(part_id__in=mooring_parts_list).filter(location_id=location_id)
            else:
                inventory_list = None
    else:
        inventory_list = None
    return render(request, 'inventory/parent_dropdown_list_options.html', {'parents': inventory_list})


# Function to load available Deployments based on Location
def load_deployments(request):
    location_id = request.GET.get('location')

    if location_id:
        deployment_list = Deployment.objects.filter(location_id=location_id)
    else:
        deployment_list = None
    return render(request, 'inventory/deployments_dropdown_list_options.html', {'deployments': deployment_list})


# Function to load available Deployments based on Location
def load_mooring_parts(request):
    deployment_id = request.GET.get('deployment')

    if deployment_id:
        deployment = Deployment.objects.get(id=deployment_id)
        mooring_parts_list = MooringPart.objects.filter(location=deployment.final_location).prefetch_related('part')
    else:
        mooring_parts_list = None
    return render(request, 'inventory/mooringparts_dropdown_list_options.html', {'mooring_parts': mooring_parts_list})


# Function to load Parts based on Part Type filter
def load_part_templates(request):
    part_type = request.GET.get('part_type')

    if part_type == 'All':
        part_list = Part.objects.all()
    else:
        part_list = Part.objects.filter(part_type=part_type)
    return render(request, 'inventory/part_templates_dropdown_list_options.html', {'parts': part_list})


# Function to load Parts based on Part Number Search
def load_part_templates_by_partnumber(request):
    part_number = request.GET.get('part_number')
    part_list = Part.objects.none()
    if part_number:
        part_list = Part.objects.filter(part_number__icontains=part_number)
    return render(request, 'inventory/part_templates_dropdown_list_options.html', {'parts': part_list, 'filter_type': 'part_number'})


# Function to load Revisions based on Part Number
def load_revisions_by_partnumber(request):
    part_id = request.GET.get('part_id')
    revisions = Revision.objects.none()
    if part_id:
        revisions = Revision.objects.filter(part_id=part_id)
    return render(request, 'inventory/revisions_dropdown_list_options.html', {'revisions': revisions,})


# Function to create Serial Number from Part Number search, load result into form to preview
def load_partnumber_create_serialnumber(request):
    part_number = request.GET.get('part_number')

    if part_number:
        part_obj = Part.objects.filter(part_number__icontains=part_number).first()
        if part_obj:
            inventory_qs = Inventory.objects.filter(part=part_obj).filter(serial_number__iregex=r'^(.*?)-[a-zA-Z0-9_]{5}$')
            if inventory_qs:
                inventory_last = inventory_qs.latest('id')
                last_serial_number_fragment = int(inventory_last.serial_number.split('-')[-1])
                new_serial_number_fragment = last_serial_number_fragment + 1
                # Fill fragment with leading zeroes if necessary
                new_serial_number_fragment = str(new_serial_number_fragment).zfill(5)
            else:
                new_serial_number_fragment = 20001
            new_serial_number = part_obj.part_number + '-' + str(new_serial_number_fragment)
        else:
            new_serial_number = ''
    else:
        new_serial_number = ''
    return render(request, 'inventory/serial_number_input.html', {'new_serial_number': new_serial_number, })


# Function to create Serial Number from Part Template selected, load result into form to preview
def load_parttemplate_create_serialnumber(request):
    part_id = request.GET.get('part_id')

    if part_id:
        part_obj = Part.objects.get(id=part_id)
        inventory_qs = Inventory.objects.filter(part=part_obj).filter(serial_number__iregex=r'^(.*?)-[a-zA-Z0-9_]{5}$')
        if inventory_qs:
            inventory_last = inventory_qs.latest('id')
            last_serial_number_fragment = int(inventory_last.serial_number.split('-')[-1])
            new_serial_number_fragment = last_serial_number_fragment + 1
            # Fill fragment with leading zeroes if necessary
            new_serial_number_fragment = str(new_serial_number_fragment).zfill(5)
        else:
            new_serial_number_fragment = 20001
        new_serial_number = part_obj.part_number + '-' + str(new_serial_number_fragment)
    else:
        new_serial_number = ''
    return render(request, 'inventory/serial_number_input.html', {'new_serial_number': new_serial_number, })


# Function to search subassembly options by serial number, load object
def load_subassemblies_by_serialnumber(request):
    serial_number = request.GET.get('serial_number').strip()
    parent_id = request.GET.get('parent_id')

    parent = Inventory.objects.get(id=parent_id)
    inventory_items = Inventory.objects.filter(serial_number__icontains=serial_number)
    return render(request, 'inventory/available_subassemblies.html', {'inventory_items': inventory_items, 'parent': parent, })


# Function to search mooring part subassembly options by serial number, load object
def load_mooringpart_subassemblies_by_serialnumber(request):
    serial_number = request.GET.get('serial_number').strip()
    parent_id = request.GET.get('parent_id')
    deployment_id = request.GET.get('deployment_id')
    mooringpart_id = request.GET.get('mooringpart_id')

    if parent_id:
        parent = Inventory.objects.get(id=parent_id)
    else:
        parent = None

    if deployment_id:
        deployment = Deployment.objects.get(id=deployment_id)
    else:
        deployment = None

    mooring_part = MooringPart.objects.get(id=mooringpart_id)
    inventory_items = Inventory.objects.filter(serial_number__icontains=serial_number).filter(part=mooring_part.part).filter(deployment__isnull=True).filter(parent__isnull=True)
    return render(request, 'inventory/available_mooringpart_subassemblies.html', {'inventory_items': inventory_items,
                                                                      'parent': parent,
                                                                      'deployment': deployment,
                                                                      'mooring_part': mooring_part, })


# Function to search destination assignment subassembly options by serial number, load object
def load_destination_subassemblies_by_serialnumber(request):
    serial_number = request.GET.get('serial_number').strip()
    parent_id = request.GET.get('parent_id')
    mooringpart_id = request.GET.get('mooringpart_id')
    location_id = request.GET.get('location_id')

    mooring_part = MooringPart.objects.get(id=mooringpart_id)
    parent = Inventory.objects.get(id=parent_id)
    location = Location.objects.get(id=location_id)
    inventory_items = Inventory.objects.filter(serial_number__icontains=serial_number).filter(part=mooring_part.part).filter(deployment__isnull=True).filter(parent__isnull=True)
    return render(request, 'inventory/available_destination_subassemblies.html', {'inventory_items': inventory_items,
                                                                      'parent': parent,
                                                                      'mooring_part': mooring_part,
                                                                      'location': location, })


# Function to return True if Part Template selected is "Equipment"
def load_is_equipment(request):
    part_id = request.GET.get('part')
    part_number = request.GET.get('part_number')

    if part_id:
        part = Part.objects.get(id=part_id)
    elif part_number:
        part = Part.objects.filter(part_number__icontains=part_number).first()
    else:
        part = None

    if part:
        is_equipment = part.is_equipment
    else:
        is_equipment = False

    data = {
        'message': "Successfully submitted form data.",
        'is_equipment': is_equipment,
    }
    return JsonResponse(data)


# Funtion to filter navtree by Part Type
def filter_inventory_navtree(request):
    part_types = request.GET.getlist('part_types[]')
    part_types = list(map(int, part_types))
    locations = Location.objects.prefetch_related('deployment__final_location__mooring_parts__part__part_type') \
                                .prefetch_related('inventory__part__part_type') \
                                .prefetch_related('deployment__inventory')
    return render(request, 'inventory/ajax_inventory_navtree.html', {'locations': locations, 'part_types': part_types})


# Inventory CBV Views for CRUD operations and menu Actions
# ------------------------------------------------------------------------------
# AJAX Views

class InventoryAjaxDetailView(LoginRequiredMixin, DetailView):
    model = Inventory
    context_object_name = 'inventory_item'
    template_name='inventory/ajax_inventory_detail.html'

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxDetailView, self).get_context_data(**kwargs)
        # Get Printers to display in print dropdown
        printers = Printer.objects.all()
        # Get this item's custom fields with most recent Values
        if self.object.fieldvalues.exists():
            custom_fields = self.object.fieldvalues.filter(is_current=True)
        else:
            custom_fields = None

        context.update({
            'printers': printers,
            'custom_fields': custom_fields,
        })
        return context


class InventoryAjaxByMooringPartDetailView(LoginRequiredMixin, DetailView):
    model = MooringPart
    context_object_name = 'mooring_part'
    template_name='inventory/ajax_inventory_detail.html'

    def get_context_data(self, **kwargs):
        context = super(InventoryByMooringPartAjaxDetailView, self).get_context_data(**kwargs)
        context.update({
            'inventory_item': Inventory.objects.get(mooring_part_id=self.kwargs['pk'])
        })
        return context


class InventoryAjaxSnapshotDetailView(LoginRequiredMixin, DetailView):
    model = Inventory
    context_object_name = 'inventory_item'
    template_name='inventory/ajax_inventory_snapshot_detail.html'


class InventoryAjaxCreateBasicView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Inventory
    form_class = InventoryAddForm
    context_object_name = 'inventory_item'
    template_name='inventory/ajax_inventory_form.html'

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.object.id,))

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxCreateBasicView, self).get_context_data(**kwargs)
        # Add Parts list to context to build form filter
        context.update({
            'part_types': PartType.objects.all()
        })
        if 'parent_pk' in self.kwargs:
            context.update({
                'parent': Inventory.objects.get(id=self.kwargs['parent_pk'])
            })
        return context

    def get_form_kwargs(self):
        kwargs = super(InventoryAjaxCreateBasicView, self).get_form_kwargs()
        if 'parent_pk' in self.kwargs:
            kwargs['parent_pk'] = self.kwargs['parent_pk']
        if 'current_location' in self.kwargs:
            kwargs['current_location'] = self.kwargs['current_location']
        return kwargs

    def get_initial(self):
        #Returns the initial data to use for forms on this view.
        initial = super(InventoryAjaxCreateBasicView, self).get_initial()
        if 'parent_pk' in self.kwargs:
            parent = Inventory.objects.get(id=self.kwargs['parent_pk'])
            part_templates = Part.objects.get(id=parent.part.id)
            if parent.deployment:
                initial['deployment'] = parent.deployment.id
            initial['parent'] = self.kwargs['parent_pk']
            initial['location'] = self.kwargs['current_location']
            initial['part'] = part_templates
        elif 'current_location' in self.kwargs:
            initial['location'] = self.kwargs['current_location']
        return initial

    def form_valid(self, form):
        self.object = form.save()
        action_record = Action.objects.create(action_type='invadd', detail='Item first added to Inventory', location_id=self.object.location_id,
                                              user_id=self.request.user.id, inventory_id=self.object.id)

        # Check if this Part has Custom fields with global default values, create fields if needed
        try:
            # Exclude any fields with Global Part Values
            custom_fields = self.object.part.user_defined_fields.exclude(fieldvalues__part=self.object.part)
        except Field.DoesNotExist:
            custom_fields = None

        if custom_fields:
            for field in custom_fields:
                if field.field_default_value:
                    # create new value object
                    fieldvalue = FieldValue.objects.create(field=field, field_value=field.field_default_value,
                                                           inventory=self.object, is_current=True, is_default_value=True)

        # Check if this Part has Custom fields with Part Template default levels, create fields if needed
        try:
            # Only fields with Default Part Values
            custom_fields = self.object.part.user_defined_fields.filter(fieldvalues__part=self.object.part) \
                                                                .filter(fieldvalues__is_current=True).distinct()
        except Field.DoesNotExist:
            custom_fields = None

        if custom_fields:
            for field in custom_fields:
                # Check if this Part has Custom fields with Part Template default levels, create fields if needed
                try:
                    default_value = field.fieldvalues.filter(part=self.object.part).latest()
                except FieldValue.DoesNotExist:
                    default_value = None

                if default_value:
                    fieldvalue = FieldValue.objects.create(field=field, field_value=default_value.field_value,
                                                                inventory=self.object, is_current=True, user=default_value.user)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
            }
            return JsonResponse(data)
        else:
            return response


class InventoryAjaxUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = Inventory
    form_class = InventoryForm
    context_object_name = 'inventory_item'
    template_name='inventory/ajax_inventory_form.html'

    def form_valid(self, form):
        self.object = form.save()

        # Check is this Part has custom fields
        if self.object.part.user_defined_fields.exists():
            # loop through all cleaned_data fields, get custom fields, update the FieldValue model
            for key, value in form.cleaned_data.items():
                # check for the 'udffield' key in string, if so proceed
                field_keys = key.partition('_')

                if field_keys[0] == 'udffield':
                    field_id = int(field_keys[2])
                    #Check if this inventory object has value for this field
                    try:
                        currentvalue = self.object.fieldvalues.filter(field_id=field_id).latest(field_name='created_at')
                    except FieldValue.DoesNotExist:
                        currentvalue = None

                    # If current value is different than new value, update is_current, add new value, add Action to History
                    if currentvalue:
                        if currentvalue.field_value != str(value):
                            currentvalue.is_current = False
                            currentvalue.save()
                            # create new value object
                            new_fieldvalue = FieldValue.objects.create(field_id=field_id, field_value=value,
                                                                        inventory=self.object, is_current=True, user=self.request.user)
                            # create action record for history
                            self.object.detail = 'Change field value for "%s" to %s' % (currentvalue.field, value)
                            self.object.save()
                            action_record = Action.objects.create(action_type='fieldchange', detail=self.object.detail, location=self.object.location,
                                                                  user=self.request.user, inventory=self.object)
                    else:
                        # create new value object
                        fieldvalue = FieldValue.objects.create(field_id=field_id, field_value=value,
                                                                inventory=self.object, is_current=True, user=self.request.user)
                        # create action record for history
                        self.object.detail = 'Add initial field value for "%s" to %s' % (fieldvalue.field, value)
                        self.object.save()
                        action_record = Action.objects.create(action_type='fieldchange', detail=self.object.detail, location=self.object.location,
                                                              user=self.request.user, inventory=self.object)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.object.id,))


class InventoryAjaxActionView(InventoryAjaxUpdateView):

    def get_form_class(self):
        ACTION_FORMS = {
            "invchange" : ActionInventoryChangeForm,
            "locationchange" : ActionLocationChangeForm,
            "subchange" : ActionSubassemblyChangeForm,
            "removefromdeployment" : ActionRemoveFromDeploymentForm,
            "removedest" : ActionRemoveDestinationForm,
            "test" : ActionTestForm,
            "note" : ActionNoteForm,
            "flag" : ActionFlagForm,
            "movetotrash" : ActionMoveToTrashForm,
        }
        action_type = self.kwargs['action_type']
        form_class_name = ACTION_FORMS[action_type]

        return form_class_name

    def form_valid(self, form):
        if self.kwargs['action_type'] == 'locationchange':
            # Find previous location to add to Detail field text
            old_location_pk = self.object.tracker.previous('location')
            if old_location_pk:
                old_location = Location.objects.get(pk=old_location_pk)
                if old_location.name != self.object.location.name:
                    self.object.detail = 'Moved to %s from %s. ' % (self.object.location.name, old_location) + self.object.detail

            # Get any subassembly children items, move their location sto match parent and add Action to history
            subassemblies = Inventory.objects.get(id=self.object.id).get_descendants()
            mooring_parts_added = []
            for item in subassemblies:
                if self.object.mooring_part_id:
                    sub_mooring_parts = MooringPart.objects.get(id=self.object.mooring_part_id).get_descendants()
                    sub_mooring_part = sub_mooring_parts.filter(part=item.part)
                    for sub in sub_mooring_part:
                        if sub.id not in mooring_parts_added:
                            item.mooring_part = sub
                            mooring_parts_added.append(sub.id)
                            break
                else:
                    item.mooring_part = None

                item.location_id = self.object.location_id
                if old_location.name != self.object.location.name:
                    item.detail = 'Moved to %s from %s' % (self.object.location.name, old_location.name)
                else:
                    item.detail = 'Parent Inventory Change'
                item.save()
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=item.detail, location_id=item.location_id,
                                                      user_id=self.request.user.id, inventory_id=item.id)

        if self.kwargs['action_type'] == 'removefromdeployment':
            # Find Deployment it was removed from
            old_deployment_pk = self.object.tracker.previous('deployment')
            if old_deployment_pk:
                old_deployment = Deployment.objects.get(pk=old_deployment_pk)
                self.object.detail = ' Removed from %s.' % (old_deployment.get_deployment_label()) + self.object.detail

            # Get any subassembly children items, add Action to history
            subassemblies = Inventory.objects.get(id=self.object.id).get_descendants()
            for item in subassemblies:
                item.mooring_part = None
                item.deployment = None
                item.location = self.object.location
                item.detail = ' Removed from %s.' % (old_deployment.get_deployment_label())
                item.save()
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=item.detail, location_id=item.location_id,
                                                      user_id=self.request.user.id, inventory_id=item.id)

        if self.kwargs['action_type'] == 'removedest':
            self.object.detail = 'Destination Assignment removed.'
            # Get any subassembly children items, add Action to history
            subassemblies = Inventory.objects.get(id=self.object.id).get_descendants()
            for item in subassemblies:
                item.mooring_part = None
                item.assigned_destination_root = None
                item.detail = 'Destination Assignment removed.'
                item.save()
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=item.detail, location_id=item.location_id,
                                                      user_id=self.request.user.id, inventory_id=item.id)

        if self.kwargs['action_type'] == 'invchange':
            # Find if it was removed from Deployment. Add note.
            old_deployment_pk = self.object.tracker.previous('deployment')
            if old_deployment_pk:
                old_deployment = Deployment.objects.get(pk=old_deployment_pk)
                self.object.detail = ' Removed from %s.' % (old_deployment.get_deployment_label()) + self.object.detail


            # Find if it was removed from Parent assembly. Add note.
            old_parent_pk = self.object.tracker.previous('parent')
            if old_parent_pk:
                old_parent = Inventory.objects.get(pk=old_parent_pk)
                parent_detail = 'Subassembly %s removed. ' % (self.object) + self.object.detail
                # Add Action Record for Parent Assembly
                action_record = Action.objects.create(action_type='subchange', detail=parent_detail, location_id=old_parent.location_id,
                                                      user_id=self.request.user.id, inventory_id=old_parent_pk)
                # Add note to instance Detail field for Action Record
                self.object.detail = 'Removed from %s.' % (old_parent) + self.object.detail

            # Find if it was added to Parent assembly. Add note.
            if self.object.parent:
                parent_detail = 'Subassembly %s added. ' % (self.object) + self.object.detail
                # Add Action Record for Parent Assembly
                action_record = Action.objects.create(action_type='subchange', detail=parent_detail, location_id=self.object.parent.location_id,
                                                      user_id=self.request.user.id, inventory_id=self.object.parent.id)

            # Find previous location to add to Detail field text
            old_location_pk = self.object.tracker.previous('location')
            if old_location_pk:
                old_location = Location.objects.get(pk=old_location_pk)
                if self.object.deployment:
                    self.object.detail = 'Moved to %s from %s' % (self.object.deployment, old_location.name) + self.object.detail
                elif old_location.name != self.object.location.name:
                    self.object.detail = 'Moved to %s from %s. ' % (self.object.location.name, old_location) + self.object.detail

            # Get any subassembly children items, move their location to match parent and add Action to history
            subassemblies = Inventory.objects.get(id=self.object.id).get_descendants()
            mooring_parts_added = []
            for item in subassemblies:
                if self.object.mooring_part_id:
                    sub_mooring_parts = MooringPart.objects.get(id=self.object.mooring_part_id).get_descendants()
                    sub_mooring_part = sub_mooring_parts.filter(part=item.part)
                    for sub in sub_mooring_part:
                        if sub.id not in mooring_parts_added:
                            item.mooring_part = sub
                            mooring_parts_added.append(sub.id)
                            break
                else:
                    item.mooring_part = None

                item.location_id = self.object.location_id
                item.deployment_id = self.object.deployment_id
                if self.object.deployment:
                    item.detail = 'Moved to %s from %s' % (self.object.deployment, old_location.name)
                elif old_location.name != self.object.location.name:
                    item.detail = 'Moved to %s from %s' % (self.object.location.name, old_location.name)
                else:
                    item.detail = 'Parent Inventory Change'
                item.save()
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=item.detail, location_id=item.location_id,
                                                      user_id=self.request.user.id, inventory_id=item.id)

        elif self.kwargs['action_type'] == 'test':
            self.object.detail = '%s: %s. ' % (self.object.get_test_type_display(), self.object.get_test_result_display()) + self.object.detail

        #elif self.kwargs['action_type'] == 'flag':
            #self.kwargs['action_type'] = self.object.get_flag_display()

        elif self.kwargs['action_type'] == 'subchange':
            # Find previous parent to add to Detail field text
            old_parent_pk = self.object.tracker.previous('parent')
            if old_parent_pk:
                old_parent = Inventory.objects.get(pk=old_parent_pk)
                parent_detail = 'Subassembly %s removed. ' % (self.object) + self.object.detail
                self.object.detail = 'Removed from %s. ' % (old_parent) + self.object.detail

                # Add Action Record for Parent Assembly
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=parent_detail, location_id=self.object.location_id,
                                                      user_id=self.request.user.id, inventory_id=old_parent_pk)

            # Find previous location to add to Detail field text
            old_location_pk = self.object.tracker.previous('location')
            if old_location_pk:
                old_location = Location.objects.get(pk=old_location_pk)
                if self.object.deployment:
                    self.object.detail = 'Moved to %s from %s' % (self.object.deployment, old_location.name) + self.object.detail
                elif old_location.name != self.object.location.name:
                    self.object.detail = 'Moved to %s from %s. ' % (self.object.location.name, old_location) + self.object.detail

            # Get any subassembly children items, move their location to match parent and add Action to history
            subassemblies = Inventory.objects.get(id=self.object.id).get_descendants()
            mooring_parts_added = []
            for item in subassemblies:
                if self.object.mooring_part_id:
                    sub_mooring_parts = MooringPart.objects.get(id=self.object.mooring_part_id).get_descendants()
                    sub_mooring_part = sub_mooring_parts.filter(part=item.part)
                    for sub in sub_mooring_part:
                        if sub.id not in mooring_parts_added:
                            item.mooring_part = sub
                            mooring_parts_added.append(sub.id)
                            break
                else:
                    item.mooring_part = None

                item.location = self.object.location
                item.deployment = self.object.deployment
                item.assigned_destination_root = self.object.assigned_destination_root

                if self.object.deployment:
                    item.detail = 'Moved to %s from %s' % (self.object.deployment, old_location.name)
                elif old_location.name != self.object.location.name:
                    item.detail = 'Moved to %s from %s' % (self.object.location.name, old_location.name)
                else:
                    item.detail = 'Parent Inventory Change'
                item.save()
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=item.detail, location_id=item.location_id,
                                                      user_id=self.request.user.id, inventory_id=item.id)

        action_form = form.save()
        action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=self.object.detail, location_id=self.object.location_id,
                                              user_id=self.request.user.id, inventory_id=self.object.id)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'location_id': self.object.location.id,
            }
            return JsonResponse(data)
        else:
            return response


class ActionNoteAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Action
    form_class = ActionPhotoNoteForm
    context_object_name = 'action'
    template_name='inventory/ajax_inventory_photo_note_form.html'

    def get_context_data(self, **kwargs):
        context = super(ActionNoteAjaxCreateView, self).get_context_data(**kwargs)
        inventory_item = Inventory.objects.get(id=self.kwargs['pk'])
        context.update({
            'inventory_item': inventory_item
        })
        return context

    def get_initial(self):
        inventory_item = Inventory.objects.get(id=self.kwargs['pk'])
        return { 'inventory': inventory_item.id, 'location': inventory_item.location_id }

    def form_valid(self, form):
        self.object = form.save()
        self.object.user_id = self.request.user.id
        self.object.action_type = 'note'
        self.object.save()

        photo_ids = form.cleaned_data['photo_ids']
        if photo_ids:
            photo_ids = photo_ids.split(',')
            for id in photo_ids:
                photo = PhotoNote.objects.get(id=id)
                photo.action_id = self.object.id
                photo.save()

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.inventory_id,
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.object.inventory_id, ))


class ActionPhotoUploadAjaxCreateView(View):
    def get(self, request, **kwargs):
        inventory_item = Inventory.objects.get(id=self.kwargs['pk'])
        form = ActionPhotoUploadForm()
        return render(self.request, 'inventory/ajax_inventory_photo_note_form.html', {'inventory_item': inventory_item,})

    def post(self, request, **kwargs):
        form = ActionPhotoUploadForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            photo_note = form.save()
            photo_note.inventory_id = self.kwargs['pk']
            photo_note.user_id = self.request.user.id
            photo_note.save()
            data = {'is_valid': True,
                    'name': photo_note.photo.name,
                    'url': photo_note.photo.url,
                    'photo_id': photo_note.id,
                    'file_type': photo_note.file_type() }
        else:
            data = {'is_valid': False}
        return JsonResponse(data)


class ActionHistoryNoteAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Action
    form_class = ActionHistoryNoteForm
    context_object_name = 'action'
    template_name='inventory/ajax_inventory_form.html'

    def get_context_data(self, **kwargs):
        context = super(ActionHistoryNoteAjaxCreateView, self).get_context_data(**kwargs)
        inventory_item = Inventory.objects.get(id=self.kwargs['pk'])
        context.update({
            'inventory_item': inventory_item
        })
        return context

    def get_initial(self):
        return {'inventory': self.kwargs['pk']}

    def form_valid(self, form):
        self.object = form.save()
        self.object.user_id = self.request.user.id
        self.object.action_type = 'historynote'
        self.object.save()

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.inventory_id,
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse('inventory:ajax_inventory_detail', args=(self.object.inventory_id, ))


class InventoryAjaxAddToDeploymentListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/ajax_inventory_add_to_deployment.html'

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxAddToDeploymentListView, self).get_context_data(**kwargs)
        inventory_item = Inventory.objects.get(id=self.kwargs['pk'])
        deployments = Deployment.objects.all().order_by('location__name')

        for dep in deployments:
            if dep.current_deployment_status() != 'create' and dep.current_deployment_status() != 'burnin':
                deployments = deployments.exclude(id=dep.id)

        if inventory_item.mooring_part:
            for dep in deployments:
                for mp in dep.final_location.mooring_parts.all():
                    if mp != inventory_item.mooring_part:
                        x = False
                    else:
                        x = True
                        break
                if not x:
                    deployments = deployments.exclude(id=dep.id)
        else:
            for dep in deployments:
                for mp in dep.final_location.mooring_parts.all():
                    if mp.part != inventory_item.part:
                        x = False
                    else:
                        x = True
                        break
                if not x:
                    deployments = deployments.exclude(id=dep.id)

        deployments = deployments.prefetch_related('final_location__mooring_parts__part')

        if inventory_item.mooring_part:
            mooring_parts = MooringPart.objects.filter(id=inventory_item.mooring_part.id)
        else:
            mooring_parts = MooringPart.objects.filter(part=inventory_item.part).filter(location__final_deployment__in=deployments).select_related().distinct()

        context.update({
            'inventory_item': inventory_item
        })
        context.update({
            'mooring_parts': mooring_parts
        })
        context.update({
            'deployments': deployments
        })
        return context


class InventoryAjaxAddToDeploymentActionView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        mooring_part = MooringPart.objects.get(id=self.kwargs['mooring_part_pk'])
        inventory_item = Inventory.objects.get(id=self.kwargs['pk'])
        deployment = Deployment.objects.get(id=self.kwargs['deployment_pk'])

        if mooring_part.parent:
            try:
                parent = Inventory.objects.filter(mooring_part=mooring_part.parent).filter(deployment=deployment).first()
            except Inventory.DoesNotExist:
                parent = None
        else:
            parent = None

        inventory_item.mooring_part = mooring_part
        inventory_item.deployment = deployment
        inventory_item.parent = parent
        inventory_item.location = deployment.location
        inventory_item.save()

        detail = 'Moved to %s.' % (inventory_item.deployment)
        # Find previous location to add to Detail field text
        old_location_pk = inventory_item.tracker.previous('location')
        if old_location_pk != inventory_item.location:
            detail = detail + ' Moved to %s.' % (inventory_item.location)
        if inventory_item.parent:
            detail = detail + ' Added to %s' % (inventory_item.parent)
            parent_record = Action.objects.create(action_type='subchange', detail='Subassembly %s added.' % (inventory_item), location_id=inventory_item.location_id,
                                                  user_id=self.request.user.id, inventory_id=inventory_item.parent.id)
        action_record = Action.objects.create(action_type='addtodeployment', detail=detail, location_id=inventory_item.location_id,
                                              user_id=self.request.user.id, inventory_id=inventory_item.id)

        # Check if any subassembly orphan children items already exist.  If so, make this item the parent
        children = inventory_item.mooring_part.get_children()
        for child in children:
            if child.inventory.exists():
                child_item = Inventory.objects.filter(mooring_part=child).filter(deployment=inventory_item.deployment)
                for c in child_item:
                    if c.deployment == inventory_item.deployment:
                        c.parent = subassembly
                        c.save()

        # Get any subassembly children items, move their location to match parent and add Action to history
        subassemblies = Inventory.objects.get(id=inventory_item.id).get_descendants()
        mooring_parts_added = []
        for item in subassemblies:
            sub_mooring_parts = inventory_item.mooring_part.get_descendants()
            sub_mooring_part = sub_mooring_parts.filter(part=item.part)

            for sub in sub_mooring_part:
                if sub.id not in mooring_parts_added:
                    item.mooring_part = sub
                    mooring_parts_added.append(sub.id)
                    break

            item.location = inventory_item.location
            item.deployment = inventory_item.deployment

            if item.deployment:
                item.detail = 'Moved to %s' % (item.deployment)
            else:
                item.detail = 'Parent Inventory Change'

            item.save()
            action_record = Action.objects.create(action_type='invchange', detail=item.detail, location_id=item.location_id,
                                                  user_id=self.request.user.id, inventory_id=item.id)

        return reverse('inventory:ajax_inventory_detail', args=(self.kwargs['pk'], ) )


class InventoryAjaxAssignDestinationView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/ajax_inventory_assign_destination.html'

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxAssignDestinationView, self).get_context_data(**kwargs)
        inventory_item = Inventory.objects.get(id=self.kwargs['pk'])
        mooring_parts = MooringPart.objects.filter(part=inventory_item.part).order_by('location__parent__name', 'location__name').select_related()

        context.update({
            'inventory_item': inventory_item
        })
        context.update({
            'mooring_parts': mooring_parts
        })
        return context


class InventoryAjaxAssignDestinationActionView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        mooring_part = MooringPart.objects.get(id=self.kwargs['mooring_part_pk'])
        inventory_item = Inventory.objects.get(id=self.kwargs['pk'])

        inventory_item.mooring_part = mooring_part
        inventory_item.assigned_destination_root = inventory_item
        inventory_item.save()

        # Get any subassembly children items, move their Mooring Part assignment to match parent
        subassemblies = inventory_item.get_descendants()
        mooring_parts_added = []
        for item in subassemblies:
            item.assigned_destination_root = inventory_item
            sub_mooring_parts = inventory_item.mooring_part.get_descendants()
            sub_mooring_part = sub_mooring_parts.filter(part=item.part)
            for sub in sub_mooring_part:
                if sub.id not in mooring_parts_added:
                    item.mooring_part = sub
                    mooring_parts_added.append(sub.id)
                    break
            item.save()

        detail = 'Destination assigned - %s.' % (inventory_item.mooring_part.location.name)
        action_record = Action.objects.create(action_type='assigndest', detail=detail, location_id=inventory_item.location_id,
                                              user_id=self.request.user.id, inventory_id=inventory_item.id)

        return reverse('inventory:ajax_inventory_detail', args=(self.kwargs['pk'], ) )


class InventoryAjaxDestinationSubassemblyListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/ajax_inventory_destination_add_subassembly.html'

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxDestinationSubassemblyListView, self).get_context_data(**kwargs)
        navtree_node_id = self.request.GET.get('navTreeNodeID')
        mooring_part = MooringPart.objects.get(id=self.kwargs['pk'])
        location = Location.objects.get(id=self.kwargs['location_pk'])
        assigned_destination_root = Inventory.objects.get(id=self.kwargs['assigned_destination_root_pk'])

        #navtreedata = json.loads(navtree_node_id)

        if mooring_part.parent:
            try:
                parent = Inventory.objects.filter(mooring_part=mooring_part.parent).filter(deployment__isnull=True).first()
            except Inventory.DoesNotExist:
                parent = None
        else:
            parent = None
        inventory_items = Inventory.objects.filter(part=mooring_part.part).filter(deployment__isnull=True).filter(parent__isnull=True).exclude(location__root_type='Trash')

        context.update({
            'inventory_items': inventory_items,
            'navtree_node_id': navtree_node_id,
            'mooring_part': mooring_part,
            'parent': parent,
            'location': location,
            'assigned_destination_root': assigned_destination_root,
        })
        return context


class InventoryAjaxDestinationSubassemblyActionView(LoginRequiredMixin, RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        subassembly = Inventory.objects.get(id=self.kwargs['pk'])
        mooring_part = MooringPart.objects.get(id=self.kwargs['mooring_part_pk'])
        location = Location.objects.get(id=self.kwargs['location_pk'])
        assigned_destination_root = Inventory.objects.get(id=self.kwargs['assigned_destination_root_pk'])

        if 'parent_pk' in self.kwargs:
            parent = Inventory.objects.get(id=self.kwargs['parent_pk'])
        else:
            parent = None

        subassembly.location = location
        subassembly.mooring_part = mooring_part
        subassembly.parent = parent
        subassembly.assigned_destination_root = assigned_destination_root
        subassembly.save()

        detail = 'Destination assigned - %s.' % (subassembly.mooring_part.location.name)
        # Find previous location to add to Detail field text
        old_location_pk = subassembly.tracker.previous('location')
        if old_location_pk != subassembly.location:
            detail = ' Moved to %s.' % (subassembly.location)
        if subassembly.parent:
            detail = detail + ' Added to %s' % (subassembly.parent)
            parent_record = Action.objects.create(action_type='subchange', detail='Subassembly %s added.' % (subassembly), location_id=subassembly.location_id,
                                                  user_id=self.request.user.id, inventory_id=subassembly.parent.id)
        action_record = Action.objects.create(action_type='invchange', detail=detail, location_id=subassembly.location_id,
                                              user_id=self.request.user.id, inventory_id=subassembly.id)

        # Check if any subassembly orphan children items already exist.  If so, make this item the parent
        children = subassembly.mooring_part.get_children()
        for child in children:
            if child.inventory.exists():
                child_item = Inventory.objects.filter(mooring_part=child).filter(assigned_destination_root=subassembly.assigned_destination_root)
                for c in child_item:
                    if c.assigned_destination_root == subassembly.assigned_destination_root:
                        c.parent = subassembly
                        c.save()

        # Get any subassembly children items, move their location to match parent and add Action to history
        subassemblies = Inventory.objects.get(id=subassembly.id).get_descendants()
        mooring_parts_added = []
        for item in subassemblies:
            sub_mooring_parts = subassembly.mooring_part.get_descendants()
            sub_mooring_part = sub_mooring_parts.filter(part=item.part)

            for sub in sub_mooring_part:
                if sub.id not in mooring_parts_added:
                    item.mooring_part = sub
                    mooring_parts_added.append(sub.id)
                    break

            item.location = subassembly.location
            item.deployment = subassembly.deployment
            item.assigned_destination_root = subassembly.assigned_destination_root

            if item.deployment:
                item.detail = 'Moved to %s' % (item.deployment)
            else:
                item.detail = 'Parent Inventory Change'

            item.save()
            action_record = Action.objects.create(action_type='invchange', detail=item.detail, location_id=item.location_id,
                                                  user_id=self.request.user.id, inventory_id=item.id)

        return reverse('inventory:ajax_inventory_detail', args=(self.kwargs['pk'], ) )


class InventoryAjaxParentListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/ajax_inventory_add_to_parent.html'

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxParentListView, self).get_context_data(**kwargs)
        item = Inventory.objects.get(id=self.kwargs['pk'])
        items_with_mooring_part = Inventory.objects.filter(part=item.part).filter(mooring_part__isnull=False)

        mooring_parts = MooringPart.objects.filter(part=item.part)
        mooring_parts_list = []
        for mp in mooring_parts:
            parent = MooringPart.objects.get(id=mp.id).get_ancestors().last()
            mooring_parts_list.append(parent)
        part_templates = Part.objects.filter(mooring_parts__in=mooring_parts_list)
        parent_items = Inventory.objects.filter(part__in=part_templates).filter(deployment__isnull=True).exclude(location__root_type='Trash').order_by('part__name')

        for parent in parent_items:
            # Check if the mooring part template spot is already filled, remove parent from queryset
            children = parent.get_children()
            if children:
                for child in children:
                    if child in items_with_mooring_part:
                        parent_items = parent_items.exclude(id=parent.id)

        for parent in parent_items:
            # Check if the parent is assigned a destination that has no mooring template spot for the item, remove from queryset
            if parent.mooring_part:
                parent_tree = parent.mooring_part.get_children()
                if parent_tree:
                    for mp in parent_tree:
                        if mp not in item.part.mooring_parts.all():
                            x = False
                        else:
                            x = True
                            break
                    if not x:
                        parent_items = parent_items.exclude(id=parent.id)

        context.update({
            'parent_items': parent_items
        })
        context.update({
            'inventory_item': item
        })
        return context


class InventoryAjaxParentActionView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        subassembly = Inventory.objects.get(id=self.kwargs['pk'])
        parent = Inventory.objects.get(id=self.kwargs['parent_pk'])
        if parent.mooring_part:
            mooring_parts = parent.mooring_part.get_children()
            mooring_part = mooring_parts.get(part=subassembly.part)
        else:
            mooring_part = None

        subassembly.location = parent.location
        subassembly.deployment = parent.deployment
        subassembly.parent = parent
        subassembly.mooring_part = mooring_part
        subassembly.assigned_destination_root = parent.assigned_destination_root
        subassembly.save()

        detail = 'Added to %s.' % (parent)
        if subassembly.deployment:
            detail = detail + ' Moved to %s' % (subassembly.deployment)
        parent_detail = 'Subassembly %s added.' % (subassembly)
        action_record = Action.objects.create(action_type='subchange', detail=detail, location_id=parent.location.id,
                                              user_id=self.request.user.id, inventory_id=subassembly.id)
        parent_action_record = Action.objects.create(action_type='subchange', detail=parent_detail, location_id=parent.location.id,
                                              user_id=self.request.user.id, inventory_id=parent.id)

        # Get any subassembly children items, move their location to match parent and add Action to history
        subassemblies = subassembly.get_descendants()
        mooring_parts_added = []
        for item in subassemblies:
            if mooring_part:
                sub_mooring_parts = subassembly.mooring_part.get_descendants()
                sub_mooring_part = sub_mooring_parts.filter(part=item.part)
                for sub in sub_mooring_part:
                    if sub.id not in mooring_parts_added:
                        item.mooring_part = sub
                        mooring_parts_added.append(sub.id)
                        break

            item.location = subassembly.location
            item.deployment = subassembly.deployment
            item.assigned_destination_root = subassembly.assigned_destination_root

            if item.deployment:
                item.detail = 'Moved to %s' % (item.deployment)
            else:
                item.detail = 'Parent Inventory Change'

            item.save()
            action_record = Action.objects.create(action_type='invchange', detail=item.detail, location_id=item.location_id,
                                                  user_id=self.request.user.id, inventory_id=item.id)

        return reverse('inventory:ajax_inventory_detail', args=(self.kwargs['pk'], ) )


class InventoryAjaxSubassemblyListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/ajax_inventory_add_subassembly.html'

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxSubassemblyListView, self).get_context_data(**kwargs)
        parent = Inventory.objects.get(id=self.kwargs['parent_pk'])
        if parent.mooring_part_id:
            mooring_parts = MooringPart.objects.get(id=parent.mooring_part_id).get_children()
            part_templates = Part.objects.filter(mooring_parts__in=mooring_parts)
            inventory_items = Inventory.objects.filter(part__in=part_templates).filter(deployment__isnull=True).exclude(location__root_type='Trash')
        else:
            mooring_parts = MooringPart.objects.filter(part=parent.part)
            mooring_parts_list = []
            for mp in mooring_parts:
                result_list = MooringPart.objects.get(id=mp.id).get_children()
                mooring_parts_list = list(chain(mooring_parts_list, result_list))
            part_templates = Part.objects.filter(mooring_parts__in=mooring_parts_list)
            inventory_items = Inventory.objects.filter(part__in=part_templates).filter(mooring_part__isnull=True).filter(parent__isnull=True).exclude(location__root_type='Trash')

        context.update({
            'inventory_items': inventory_items
        })
        context.update({
            'parent': parent
        })
        return context


class InventoryAjaxSubassemblyActionView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        subassembly = Inventory.objects.get(id=self.kwargs['pk'])
        parent = Inventory.objects.get(id=self.kwargs['parent_pk'])
        if parent.mooring_part_id:
            mooring_parts = MooringPart.objects.get(id=parent.mooring_part_id).get_children()
            mooring_part = mooring_parts.get(part=subassembly.part)
        else:
            mooring_part = None

        subassembly.location = parent.location
        subassembly.deployment = parent.deployment
        subassembly.parent = parent
        subassembly.mooring_part = mooring_part
        subassembly.save()

        detail = 'Added to %s.' % (parent)
        if subassembly.deployment:
            detail = detail + ' Moved to %s' % (subassembly.deployment)
        parent_detail = 'Subassembly %s added.' % (subassembly)
        action_record = Action.objects.create(action_type='subchange', detail=detail, location_id=parent.location.id,
                                              user_id=self.request.user.id, inventory_id=subassembly.id)
        parent_action_record = Action.objects.create(action_type='subchange', detail=parent_detail, location_id=parent.location.id,
                                              user_id=self.request.user.id, inventory_id=parent.id)

        # Get any subassembly children items, move their location to match parent and add Action to history
        subassemblies = Inventory.objects.get(id=subassembly.id).get_descendants()
        mooring_parts_added = []
        for item in subassemblies:
            if mooring_part:
                sub_mooring_parts = subassembly.mooring_part.get_descendants()
                sub_mooring_part = sub_mooring_parts.filter(part=item.part)
                for sub in sub_mooring_part:
                    if sub.id not in mooring_parts_added:
                        item.mooring_part = sub
                        mooring_parts_added.append(sub.id)
                        break

            item.location = subassembly.location
            item.deployment = subassembly.deployment

            if item.deployment:
                item.detail = 'Moved to %s' % (item.deployment)
            else:
                item.detail = 'Parent Inventory Change'

            item.save()
            action_record = Action.objects.create(action_type='invchange', detail=item.detail, location_id=item.location_id,
                                                  user_id=self.request.user.id, inventory_id=item.id)

        return reverse('inventory:ajax_inventory_detail', args=(self.kwargs['parent_pk'], ) )


class InventoryByMooringPartAjaxSubassemblyListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/ajax_inventory_mooringpart_add_subassembly.html'

    def get_context_data(self, **kwargs):
        context = super(InventoryByMooringPartAjaxSubassemblyListView, self).get_context_data(**kwargs)
        mooring_part = MooringPart.objects.get(id=self.kwargs['pk'])
        location = Location.objects.get(id=self.kwargs['location_pk'])
        deployment = Deployment.objects.get(id=self.kwargs['deployment_pk'])
        if mooring_part.parent:
            try:
                parent = Inventory.objects.filter(mooring_part=mooring_part.parent).filter(deployment=deployment).first()
            except Inventory.DoesNotExist:
                parent = None
        else:
            parent = None
        inventory_items = Inventory.objects.filter(part=mooring_part.part).filter(deployment__isnull=True).filter(parent__isnull=True).exclude(location__root_type='Trash')
        inventory_items = inventory_items.filter(Q(mooring_part = mooring_part) | Q(mooring_part__isnull = True))

        context.update({
            'inventory_items': inventory_items
        })
        context.update({
            'mooring_part': mooring_part
        })
        context.update({
            'parent': parent
        })
        context.update({
            'location': location
        })
        context.update({
            'deployment': deployment
        })

        return context


class InventoryByMooringPartAjaxSubassemblyActionView(LoginRequiredMixin, RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        subassembly = Inventory.objects.get(id=self.kwargs['pk'])
        mooring_part = MooringPart.objects.get(id=self.kwargs['mooring_part_pk'])
        deployment = Deployment.objects.get(id=self.kwargs['deployment_pk'])
        location = deployment.location
        if 'parent_pk' in self.kwargs:
            parent = Inventory.objects.get(id=self.kwargs['parent_pk'])
        else:
            parent = None

        subassembly.location = location
        subassembly.deployment = deployment
        subassembly.future_destination = None
        subassembly.parent = parent
        subassembly.mooring_part = mooring_part
        subassembly.save()

        detail = 'Moved to %s.' % (subassembly.deployment)
        if subassembly.parent:
            detail = detail + ' Added to %s' % (subassembly.parent)
            parent_record = Action.objects.create(action_type='subchange', detail='Subassembly %s added.' % (subassembly), location_id=subassembly.location_id,
                                                  user_id=self.request.user.id, inventory_id=subassembly.parent.id)
        action_record = Action.objects.create(action_type='invchange', detail=detail, location_id=subassembly.location_id,
                                              user_id=self.request.user.id, inventory_id=subassembly.id)

        # Check if any subassembly orphan children items already exist.  If so, make this item the parent
        children = subassembly.mooring_part.get_children()
        for child in children:
            if child.inventory.exists():
                child_item = Inventory.objects.filter(mooring_part=child).filter(deployment=subassembly.deployment)
                for c in child_item:
                    if c.deployment == subassembly.deployment:
                        c.parent = subassembly
                        c.save()


        # Get any subassembly children items, move their location to match parent and add Action to history
        subassemblies = Inventory.objects.get(id=subassembly.id).get_descendants()
        mooring_parts_added = []
        for item in subassemblies:
            sub_mooring_parts = subassembly.mooring_part.get_descendants()
            sub_mooring_part = sub_mooring_parts.filter(part=item.part)

            for sub in sub_mooring_part:
                if sub.id not in mooring_parts_added:
                    item.mooring_part = sub
                    mooring_parts_added.append(sub.id)
                    break

            item.location = subassembly.location
            item.deployment = subassembly.deployment

            if item.deployment:
                item.detail = 'Moved to %s' % (item.deployment)
            else:
                item.detail = 'Parent Inventory Change'

            item.save()
            action_record = Action.objects.create(action_type='invchange', detail=item.detail, location_id=item.location_id,
                                                  user_id=self.request.user.id, inventory_id=item.id)

        return reverse('inventory:ajax_inventory_detail', args=(self.kwargs['pk'], ) )


class InventoryAjaxLocationDetailView(LoginRequiredMixin, DetailView):
    model = Location
    template_name = 'inventory/ajax_inventory_location_detail.html'
    context_object_name = 'location'


class InventoryAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Inventory
    context_object_name = 'inventory_item'
    template_name = 'inventory/ajax_inventory_confirm_delete.html'
    success_url = reverse_lazy('inventory:inventory_home')
    permission_required = 'inventory.delete_inventory'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.parent_id,
        }
        self.object.delete()
        return JsonResponse(data)


# Base Views

# View to get direct link to an Inventory item
class InventoryDetailView(LoginRequiredMixin, DetailView):
    model = Inventory
    template_name='inventory/inventory_detail.html'
    context_object_name='inventory_item'

    def get_context_data(self, **kwargs):
        context = super(InventoryDetailView, self).get_context_data(**kwargs)
        # Add Parts list to context to build navtree filter
        part_types = PartType.objects.all()
        # Get Printers to display in print dropdown
        printers = Printer.objects.all()

        # Get this item's custom fields with most recent Values
        if self.object.fieldvalues.exists():
            custom_fields = self.object.fieldvalues.filter(is_current=True)
        else:
            custom_fields = None

        context.update({
            'part_types': part_types,
            'printers': printers,
            'custom_fields': custom_fields,
            'node_type': 'inventory',
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# View to get main Inventory landing page
class InventoryHomeView(LoginRequiredMixin, TemplateView):
    template_name ='inventory/inventory_list.html'
    context_object_name = 'inventory_item'

    def get_context_data(self, **kwargs):
        context = super(InventoryHomeView, self).get_context_data(**kwargs)
        # Add Parts list to context to build navtree filter
        part_types = PartType.objects.all()
        context.update({
            'part_types': part_types,
            'node_type': 'inventory',
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class InventoryHomeTestView(InventoryNavTreeMixin, TemplateView):
    template_name ='inventory/inventory_list_test.html'
    context_object_name = 'inventory_item'

    def get_context_data(self, **kwargs):
        context = super(InventoryHomeTestView, self).get_context_data(**kwargs)
        # Add Parts list to context to build navtree filter
        context.update({
            'part_types': PartType.objects.all(),
            'node_type': 'inventory'
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class InventoryCreateView(InventoryNavTreeMixin, CreateView):
    model = Inventory
    form_class = InventoryForm
    template_name='inventory/inventory_action_form.html'

    def get_success_url(self):
        return reverse('inventory:inventory_detail', args=(self.object.id, self.object.location_id))

    def get_context_data(self, **kwargs):
        context = super(InventoryCreateView, self).get_context_data(**kwargs)
        # Add Parts list to context to build form filter
        context.update({
            'part_types': PartType.objects.all()
        })
        if 'parent_pk' in self.kwargs:
            context.update({
                'parent': Inventory.objects.get(id=self.kwargs['parent_pk'])
            })
        return context

    def get_form_kwargs(self):
        kwargs = super(InventoryCreateView, self).get_form_kwargs()
        if 'parent_pk' in self.kwargs:
            kwargs['parent_pk'] = self.kwargs['parent_pk']
        if 'current_location' in self.kwargs:
            kwargs['current_location'] = self.kwargs['current_location']
        return kwargs

    def get_initial(self):
        #Returns the initial data to use for forms on this view.
        initial = super(InventoryCreateView, self).get_initial()
        if 'parent_pk' in self.kwargs:
            parent = Inventory.objects.get(id=self.kwargs['parent_pk'])
            part_templates = Part.objects.get(id=parent.part.id)
            if parent.deployment:
                initial['deployment'] = parent.deployment.id
            initial['parent'] = self.kwargs['parent_pk']
            initial['location'] = self.kwargs['current_location']
            initial['part'] = part_templates
        elif 'current_location' in self.kwargs:
            initial['location'] = self.kwargs['current_location']
        return initial

    def form_valid(self, form):
        self.object = form.save()
        action_record = Action.objects.create(action_type='invadd', detail='Item first added to Inventory', location_id=self.object.location_id,
                                              user_id=self.request.user.id, inventory_id=self.object.id)

        if 'parent_pk' in self.kwargs:
            detail = 'Subassembly %s added' % (self.object.serial_number)
            parent_action_record = Action.objects.create(action_type='subchange', detail=detail, location_id=self.object.location_id,
                                                        user_id=self.request.user.id, inventory_id=self.kwargs['parent_pk'])
        return HttpResponseRedirect(self.get_success_url())


class InventoryUpdateView(InventoryNavTreeMixin, UpdateView):
    model = Inventory
    form_class = InventoryForm
    context_object_name='inventory_item'
    template_name='inventory/inventory_action_form.html'

    def get_context_data(self, **kwargs):
        context = super(InventoryUpdateView, self).get_context_data(**kwargs)
        # Get latest detail information if part is flagged
        if Action.objects.filter( Q(action_type='flag') & Q(inventory_id=self.object.id) ).exists() and self.kwargs['action_type'] == 'flag':
            context.update({
                'latest_flag': Action.objects.filter( Q(action_type='flag') & Q(inventory_id=self.object.id) ).latest('created_at')
            })

        if 'action_type' in self.kwargs:
            context['action_type'] = self.kwargs['action_type']
        else:
            context['action_type'] = None

        return context

    def get_success_url(self):
        return reverse('inventory:inventory_detail', args=(self.object.id, self.object.location_id))


class InventoryActionView(InventoryUpdateView):

    def get_form_class(self):
        ACTION_FORMS = {
            "invchange" : ActionInventoryChangeForm,
            "subchange" : ActionSubassemblyChangeForm,
            "test" : ActionTestForm,
            "note" : ActionNoteForm,
            "flag" : ActionFlagForm,
        }
        action_type = self.kwargs['action_type']
        form_class_name = ACTION_FORMS[action_type]

        return form_class_name

    def form_valid(self, form):

        if self.kwargs['action_type'] == 'invchange':
            # Find if it was removed from Parent assembly. Add note.
            old_parent_pk = self.object.tracker.previous('parent')
            if old_parent_pk:
                old_parent = Inventory.objects.get(pk=old_parent_pk)
                parent_detail = 'Subassembly %s removed. ' % (self.object) + self.object.detail
                # Add Action Record for Parent Assembly
                action_record = Action.objects.create(action_type='subchange', detail=parent_detail, location_id=old_parent.location_id,
                                                      user_id=self.request.user.id, inventory_id=old_parent_pk)
                # Add note to instance Detail field for Action Record
                self.object.detail = 'Removed from %s.' % (old_parent) + self.object.detail

            # Find if it was added to Parent assembly. Add note.
            if self.object.parent:
                parent_detail = 'Subassembly %s added. ' % (self.object) + self.object.detail
                # Add Action Record for Parent Assembly
                action_record = Action.objects.create(action_type='subchange', detail=parent_detail, location_id=self.object.parent.location_id,
                                                      user_id=self.request.user.id, inventory_id=self.object.parent.id)

            # Find previous location to add to Detail field text
            old_location_pk = self.object.tracker.previous('location')
            if old_location_pk:
                old_location = Location.objects.get(pk=old_location_pk)
                if old_location.name != self.object.location.name:
                    self.object.detail = 'Moved to %s from %s. ' % (self.object.location.name, old_location) + self.object.detail

            # Get any subassembly children items, move their location to match parent and add Action to history
            queryset = Inventory.objects.get(id=self.object.id).get_descendants()
            for item in queryset:
                item.location_id = self.object.location_id
                item.deployment_id = self.object.deployment_id
                if old_location.name != self.object.location.name:
                    item.detail = 'Moved to %s from %s' % (self.object.location.name, old_location.name)
                else:
                    item.detail = 'Parent Inventory Change'
                item.save()
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=item.detail, location_id=item.location_id,
                                                      user_id=self.request.user.id, inventory_id=item.id)

        elif self.kwargs['action_type'] == 'test':
            self.object.detail = '%s: %s. ' % (self.object.get_test_type_display(), self.object.get_test_result_display()) + self.object.detail

        elif self.kwargs['action_type'] == 'flag':
            self.kwargs['action_type'] = self.object.get_flag_display()

        elif self.kwargs['action_type'] == 'subchange':
            # Find previous parent to add to Detail field text
            old_parent_pk = self.object.tracker.previous('parent')
            if old_parent_pk:
                old_parent = Inventory.objects.get(pk=old_parent_pk)
                parent_detail = 'Subassembly %s removed. ' % (self.object) + self.object.detail
                self.object.detail = 'Removed from %s. Moved to %s. ' % (old_parent, self.object.location.name) + self.object.detail

                # Add Action Record for Parent Assembly
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=parent_detail, location_id=self.object.location_id,
                                                      user_id=self.request.user.id, inventory_id=old_parent_pk)

        action_form = form.save()
        action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=self.object.detail, location_id=self.object.location_id,
                                              user_id=self.request.user.id, inventory_id=self.object.id)

        return HttpResponseRedirect(self.get_success_url())


class InventorySubassemblyListView(InventoryNavTreeMixin, ListView):
    model = Inventory
    template_name = 'inventory/inventory_subassembly_existing.html'
    context_object_name = 'inventory_item'

    def get_context_data(self, **kwargs):
        context = super(InventorySubassemblyListView, self).get_context_data(**kwargs)
        parent = Inventory.objects.get(id=self.kwargs['pk'])
        part_templates = Part.objects.get(id=parent.part.id).get_children()
        inventory_item = Inventory.objects.filter(part__in=part_templates).exclude(location=parent.location)

        context.update({
            'inventory_item': inventory_item
        })
        context.update({
            'parent': parent
        })

        return context


class InventorySubassemblyActionView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        subassembly = get_object_or_404(Inventory, pk=kwargs['pk'])
        parent = get_object_or_404(Inventory, pk=kwargs['parent_pk'])
        subassembly.location = parent.location
        subassembly.deployment = parent.deployment
        subassembly.parent = parent
        subassembly.save()

        return reverse('inventory:inventory_detail', args=(self.kwargs['parent_pk'], self.kwargs['current_location']) ) + '#subassemblies'


class InventoryDeleteView(DeleteView):
    model = Inventory
    success_url = reverse_lazy('inventory:inventory_home')


class InventorySearchSerialList(InventoryNavTreeMixin, ListView):
    # Display a Inventory List page filtered by serial number.
    model = Inventory
    template_name = 'inventory/inventory_search_list.html'
    context_object_name = 'inventory_item'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super(InventorySearchSerialList, self).get_context_data(**kwargs)

        # Check if search query exists, if so add it to context for pagination
        keywords = self.request.GET.get('q')

        if keywords:
            search = 'q=' + keywords
        else:
            search = None

        context.update({
            'part_types': PartType.objects.all(),
            'node_type': 'inventory',
            'search': search,
        })
        return context

    def get_queryset(self):
        qs = Inventory.objects.none()
        keywords = self.request.GET.get('q')
        if keywords:
            qs = Inventory.objects.filter(serial_number__icontains=keywords)
        return qs


class InventoryDeploymentDetailView(InventoryNavTreeMixin, DetailView):
    model = Deployment
    template_name='inventory/inventory_deployment_detail.html'
    context_object_name='deployment'
    current_location = None


####################### Deployment views ########################

# AJAX Views

def load_deployment_navtree(request):
    locations = Location.objects.exclude(root_type='Trash').prefetch_related('deployment')
    return render(request, 'inventory/ajax_deployment_navtree.html', {'locations': locations})


class DeploymentAjaxDetailView(LoginRequiredMixin, DetailView):
    model = Deployment
    context_object_name = 'deployment'
    template_name='inventory/ajax_deployment_detail.html'

    def get_context_data(self, **kwargs):
        context = super(DeploymentAjaxDetailView, self).get_context_data(**kwargs)
        # Get percent complete info
        total_mooringparts = MooringPart.objects.filter(location=self.object.final_location).count()
        total_inventory = self.object.inventory.count()
        percent_complete = round( (total_inventory / total_mooringparts) * 100 )

        # Get Lat/Long, Depth if Deployed
        action_record = DeploymentAction.objects.filter(deployment=self.object).filter(action_type='deploy')

        context.update({
            'percent_complete': percent_complete,
            'action_record': action_record,
        })
        return context


class DeploymentAjaxUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = Deployment
    form_class = DeploymentForm
    context_object_name = 'deployment'
    template_name='inventory/ajax_deployment_form.html'

    def get_context_data(self, **kwargs):
        context = super(DeploymentAjaxUpdateView, self).get_context_data(**kwargs)

        if 'action_type' in self.kwargs:
            context['action_type'] = self.kwargs['action_type']
        else:
            context['action_type'] = None

        return context

    def get_success_url(self):
        return reverse('deployments:ajax_deployment_detail', args=(self.object.id,))


class DeploymentAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Deployment
    form_class = DeploymentForm
    context_object_name = 'deployment'
    template_name='inventory/ajax_deployment_form.html'

    def get_initial(self):
        #Returns the initial data to use for forms on this view.
        initial = super(DeploymentAjaxCreateView, self).get_initial()
        if 'current_location' in self.kwargs:
            initial['location'] = self.kwargs['current_location']
        return initial

    def get_success_url(self):
        return reverse('deployments:ajax_deployment_detail', args=(self.object.id,))

    def form_valid(self, form):
        self.object = form.save()

        # Get the date for the Action Record from the custom form field
        action_date = form.cleaned_data['date']
        action_record = DeploymentAction.objects.create(action_type='create', detail='Deployment created', location_id=self.object.location_id,
                                              user_id=self.request.user.id, deployment_id=self.object.id, created_at=action_date)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
            }
            return JsonResponse(data)
        else:
            return response


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

        if action_type == 'burnin':
            self.object.detail = 'Burn In initiated at %s. ' % (self.object.location)
            action_type_inventory = 'deploymentburnin'

        if action_type == 'deploy':
            self.object.detail = 'Deployed to Sea: %s. ' % (self.object.final_location)
            action_type_inventory = 'deploymenttosea'

            # Create a Snapshot when Deployment is Deployed
            deployment = self.object
            base_location = Location.objects.get(root_type='Snapshots')
            inventory_items = deployment.inventory.all()

            snapshot = DeploymentSnapshot.objects.create(deployment=deployment,
                                                         location=base_location,
                                                         snapshot_location=deployment.location,
                                                         notes=self.object.detail)

            # Now create Inventory Item Snapshots with make_tree_copy function for Deployment Snapshot
            for item in inventory_items:
                if item.is_root_node():
                    make_tree_copy(item, base_location, snapshot, item.parent)

        if action_type == 'recover':
            self.object.detail = 'Recovered from Sea to %s. ' % (self.object.location)
            action_type_inventory = 'deploymentrecover'

        if action_type == 'retire':
            self.object.detail = 'Retired from service.'
            action_type_inventory = 'removefromdeployment'

        action_form = form.save()

        # Get the date for the Action Record from the custom form field
        action_date = form.cleaned_data['date']

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

        # Get all Inventory items on Deployment, match location and add Action
        inventory_items = Inventory.objects.filter(deployment_id=self.object.id)
        for item in inventory_items:
            item.location = action_form.location
            item.save()

            action_record = Action.objects.create(action_type=action_type_inventory, detail='', location_id=self.object.location_id,
                                                  user_id=self.request.user.id, inventory_id=item.id, created_at=action_date)
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
                'object_id': self.object.id,
                'location_id': self.object.location.id,
            }
            return JsonResponse(data)
        else:
            return response


class DeploymentAjaxSnapshotCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = DeploymentSnapshot
    form_class = DeploymentSnapshotForm
    template_name = 'inventory/ajax_snapshot_form.html'
    context_object_name = 'deployment'

    def get_context_data(self, **kwargs):
        context = super(DeploymentAjaxSnapshotCreateView, self).get_context_data(**kwargs)
        context.update({
            'deployment': Deployment.objects.get(id=self.kwargs['pk'])
        })
        return context

    def get_form_kwargs(self):
        kwargs = super(DeploymentAjaxSnapshotCreateView, self).get_form_kwargs()
        if 'pk' in self.kwargs:
            kwargs['pk'] = self.kwargs['pk']
        return kwargs

    def get_success_url(self):
        return reverse('deployments:ajax_deployment_detail', args=(self.kwargs['pk'], ))

    def form_valid(self, form, **kwargs):
        deployment = Deployment.objects.get(pk=self.kwargs['pk'])
        base_location = Location.objects.get(root_type='Snapshots')
        #snapshot_location = Location.objects.get(root_type='Snapshots')
        inventory_items = deployment.inventory.all()

        deployment_snapshot = form.save()
        deployment_snapshot.deployment = deployment
        deployment_snapshot.location = base_location
        deployment_snapshot.snapshot_location = deployment.location
        deployment_snapshot.save()

        for item in inventory_items:
            if item.is_root_node():
                make_tree_copy(item, base_location, deployment_snapshot, item.parent)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': deployment.id,
            }
            return JsonResponse(data)
        else:
            return response


class DeploymentAjaxDeleteView(DeleteView):
    model = Deployment
    template_name = 'inventory/ajax_deployment_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.location_id,
        }
        self.object.delete()
        return JsonResponse(data)


class DeploymentSnapshotAjaxDetailView(LoginRequiredMixin, DetailView):
    model = DeploymentSnapshot
    context_object_name = 'deployment_snapshot'
    template_name='inventory/ajax_deployment_snapshot_detail.html'


class DeploymentSnapshotAjaxDeleteView(DeleteView):
    model = DeploymentSnapshot
    template_name = 'inventory/ajax_deployment_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.location_id,
        }
        self.object.delete()
        return JsonResponse(data)


# Deployment Base Views

class DeploymentHomeView(LoginRequiredMixin, TemplateView):
    model = Deployment
    template_name = 'inventory/deployment_list.html'
    context_object_name = 'deployments'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(DeploymentHomeView, self).get_context_data(**kwargs)
        # Add Parts list to context to build navtree filter
        context.update({
            'node_type': 'deployments'
        })
        return context


class DeploymentDetailView(LoginRequiredMixin, DetailView):
    model = Deployment
    template_name='inventory/deployment_detail.html'
    context_object_name='deployment'
    current_location = None

    def get_context_data(self, **kwargs):
        context = super(DeploymentDetailView, self).get_context_data(**kwargs)
        # Add Parts list to context to build navtree filter
        context.update({
            'node_type': 'deployments'
        })
        return context


class DeploymentCreateView(InventoryNavTreeMixin, CreateView):
    model = Deployment
    form_class = DeploymentForm
    template_name='inventory/deployment_form.html'

    def get_initial(self):
        #Returns the initial data to use for forms on this view.
        initial = super(DeploymentCreateView, self).get_initial()
        if 'current_location' in self.kwargs:
            initial['location'] = self.kwargs['current_location']
        return initial

    def get_success_url(self):
        return reverse('deployments:deployment_detail', args=(self.object.id, self.object.location_id))


class DeploymentUpdateView(InventoryNavTreeMixin, UpdateView):
    model = Deployment
    form_class = DeploymentForm
    template_name='inventory/deployment_form.html'

    def form_valid(self, form):
        self.object = form.save()
        inventory_items = Inventory.objects.filter(deployment_id=self.object.id).update(location_id=self.object.location_id)

        return HttpResponseRedirect(self.get_success_url())


    def get_success_url(self):
        return reverse('deployments:deployment_detail', args=(self.object.id, self.object.location_id))


class DeploymentDeleteView(DeleteView):
    model = Deployment
    success_url = reverse_lazy('deployments:deployment_list')


class DeploymentDeployConfirmView(InventoryNavTreeMixin, DetailView):
    model = Deployment
    template_name = 'inventory/inventory_deployment_deploy_confirm.html'
    context_object_name='deployment'
