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
import environ
import json
import socket
import os
import xml.etree.ElementTree as ET
from dateutil import parser
from itertools import chain

from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
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

from .models import (
    Inventory,
    Deployment,
    InventoryDeployment,
    Action,
    DeploymentAction,
    InventorySnapshot,
    DeploymentSnapshot,
)
from .forms import *
from .utils import _create_action_history
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision
from roundabout.admintools.models import Printer
from roundabout.userdefinedfields.models import FieldValue, Field
from roundabout.assemblies.models import AssemblyPart
from roundabout.builds.models import Build, BuildAction
from common.util.mixins import AjaxFormMixin

# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels

labels = set_app_labels()
# Import environment variables from .env files
env = environ.Env()
# Global variables for views.py functions
node_type = "inventory"


# General Functions for Inventory
# ------------------------------------------------------------------------------


def load_inventory_navtree(request):
    node_id = request.GET.get("id")

    if node_id == "#" or not node_id:
        locations = Location.objects.prefetch_related("inventory__part__part_type")

        return render(
            request, "inventory/ajax_inventory_navtree.html", {"locations": locations}
        )
    else:
        build_pk = node_id.split("_")[1]
        build = (
            Build.objects.prefetch_related("assembly_revision__assembly_parts")
            .prefetch_related("inventory")
            .get(id=build_pk)
        )
        return render(
            request,
            "builds/build_tree_assembly.html",
            {
                "assembly_parts": build.assembly_revision.assembly_parts,
                "inventory_qs": build.inventory,
                "location_pk": build.location_id,
                "build_pk": build_pk,
            },
        )


# Function to filter navtree by Part Type
def filter_inventory_navtree(request):
    part_types = request.GET.getlist("part_types[]")
    part_types = list(map(int, part_types))
    locations = Location.objects.exclude(root_type="Retired").prefetch_related(
        "inventory__part__part_type"
    )
    return render(
        request,
        "inventory/ajax_inventory_navtree.html",
        {"locations": locations, "part_types": part_types},
    )


def make_tree_copy(root_part, new_location, deployment_snapshot, parent=None):
    # Makes a copy of the tree starting at "root_part", move to new Location, reparenting it to "parent"
    if root_part.part.friendly_name:
        part_name = root_part.part.friendly_name
    else:
        part_name = root_part.part.name

    new_item = InventorySnapshot.objects.create(
        location=new_location,
        inventory=root_part,
        parent=parent,
        deployment=deployment_snapshot,
        order=part_name,
    )

    for child in root_part.get_children():
        make_tree_copy(child, new_location, deployment_snapshot, new_item)


# Function to print to network printer via sockets
def print_code_zebraprinter(request, **kwargs):
    item_pk = kwargs.get("pk")
    code_format = kwargs.get("code_format", "QR")
    printer_name = request.GET.get("printer_name")
    printer_type = request.GET.get("printer_type")

    if printer_name and printer_type:
        # try:
        item = Inventory.objects.get(id=item_pk)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((printer_name, 9100))

        if printer_type == "Brady":
            # Need to load XML file so we'll set the path
            module_dir = os.path.dirname(__file__)  # get current directory
            # Set XML Namespace to get clean output
            ET.register_namespace("", "http://www.bradycorp.com/printers/bpl")

            if code_format == "QR":
                file_path = os.path.join(
                    module_dir, "printer_template_files/brady-qr.xml"
                )
                tree = ET.parse(file_path)
                root = tree.getroot()

                # modifying the Static Text 'value' attribute to be Serial Number
                for number, static_text in enumerate(
                    root.iter("{http://www.bradycorp.com/printers/bpl}static-text"),
                    start=1,
                ):
                    if number == 3:
                        static_text.set("value", item.part.friendly_name_display())
                    else:
                        static_text.set("value", item.serial_number)

                content = ET.tostring(root, encoding="utf8").decode("utf8")

            elif code_format == "bar93":
                file_path = os.path.join(
                    module_dir, "printer_template_files/brady-bar93.xml"
                )
                tree = ET.parse(file_path)
                root = tree.getroot()

                # modifying the Static Text 'value' attribute to be Serial Number
                for number, static_text in enumerate(
                    root.iter("{http://www.bradycorp.com/printers/bpl}static-text"),
                    start=1,
                ):
                    if number == 3:
                        static_text.set("value", item.part.friendly_name_display())
                    else:
                        static_text.set("value", item.serial_number.upper())

                content = ET.tostring(root, encoding="utf8").decode("utf8")

        elif printer_type == "Zebra":
            if code_format == "QR":
                content = "^XA \
                            ^PW400 \
                            ^FO20,20 \
                            ^BQ,2,5 \
                            ^FDMM,A{}^FS \
                            ^FO20,170 \
                            ^A0,30,25 \
                            ^FD{}^FS^XZ".format(
                    item.serial_number, item.serial_number
                )
                # content = '^XA^PW400^LL200^FO20,20^A0N,30,30~SD25^FDHello Connor^FS^XZ'
            elif code_format == "bar93":
                content = "^XA \
                            ^PW400 \
                            ^FO20,20^BY1 \
                            ^BAN,150,Y,N,N \
                            ^FD{}^FS^XZ".format(
                    item.serial_number.upper()
                )

        content = content.encode()

        s.sendall(content)
        s.close()

        success = True
        message = "Label printed."
        """
        except:
        success = False
        message = 'Printing failed. Check printer status.'
        """
    else:
        success = False
        message = "Printing failed. Check printer status."

    data = {
        "message": message,
        "success": success,
    }
    return JsonResponse(data)


# AJAX Functions for Forms
# ------------------------------------------------------------------------------

# Function to load available Parent Inventory items based on Part Template
def load_parents(request):
    part_id = request.GET.get("part")
    location_id = request.GET.get("location")

    if part_id:
        assembly_parts = AssemblyPart.objects.filter(part_id=part_id)
    else:
        assembly_parts = None

    if assembly_parts and location_id and part_id:
        assembly_parts_list = []
        for ap in assembly_parts:
            if ap.parent:
                assembly_parts_list.append(ap.parent.part.id)
                inventory_list = Inventory.objects.filter(
                    part_id__in=assembly_parts_list
                ).filter(location_id=location_id)
            else:
                inventory_list = None
    else:
        inventory_list = None
    return render(
        request,
        "inventory/parent_dropdown_list_options.html",
        {"parents": inventory_list},
    )


# Function to load available Deployments based on Location
def load_deployments(request):
    location_id = request.GET.get("location")

    if location_id:
        deployment_list = Deployment.objects.filter(location_id=location_id)
    else:
        deployment_list = None
    return render(
        request,
        "inventory/deployments_dropdown_list_options.html",
        {"deployments": deployment_list},
    )


# Function to load Parts based on Part Type filter
def load_part_templates(request):
    part_type = request.GET.get("part_type")

    if part_type == "All":
        part_list = Part.objects.all()
    else:
        part_list = Part.objects.filter(part_type=part_type)
    return render(
        request,
        "inventory/part_templates_dropdown_list_options.html",
        {"parts": part_list},
    )


# Function to load Parts based on Part Number Search
def load_part_templates_by_partnumber(request):
    part_number = request.GET.get("part_number")
    part_list = Part.objects.none()
    if part_number:
        part_list = Part.objects.filter(part_number__icontains=part_number)
    return render(
        request,
        "inventory/part_templates_dropdown_list_options.html",
        {"parts": part_list, "filter_type": "part_number"},
    )


# Function to load Revisions based on Part Number
def load_revisions_by_partnumber(request):
    part_id = request.GET.get("part_id")
    revisions = Revision.objects.none()
    if part_id:
        revisions = Revision.objects.filter(part_id=part_id)
    return render(
        request,
        "inventory/revisions_dropdown_list_options.html",
        {
            "revisions": revisions,
        },
    )


# Function to create Serial Number from Part Number search or Part Template selection , load result into form to preview
def load_new_serialnumber(request):
    # Set pattern variables from .env configuration
    RDB_SERIALNUMBER_CREATE = env.bool("RDB_SERIALNUMBER_CREATE", default=False)
    RDB_SERIALNUMBER_OOI_DEFAULT_PATTERN = env.bool(
        "RDB_SERIALNUMBER_OOI_DEFAULT_PATTERN", default=False
    )
    RDB_SERIALNUMBER_OOI_WETCABLE_PATTERN = env.bool(
        "RDB_SERIALNUMBER_OOI_WETCABLE_PATTERN", default=False
    )
    print(RDB_SERIALNUMBER_CREATE)

    # Set variables from JS request
    part_number = request.GET.get("part_number")
    part_id = request.GET.get("part_id")
    new_serial_number = ""

    if RDB_SERIALNUMBER_CREATE:
        if part_number or part_id:
            if part_number:
                part_obj = Part.objects.filter(
                    part_number__icontains=part_number
                ).first()

            if part_id:
                part_obj = Part.objects.get(id=part_id)

            if part_obj:
                if RDB_SERIALNUMBER_OOI_DEFAULT_PATTERN:
                    # Check if this a Cable, set the serial number variables accordingly
                    if (
                        RDB_SERIALNUMBER_OOI_WETCABLE_PATTERN
                        and part_obj.part_type.name == "Cable"
                    ):
                        regex = "^(.*?)-[a-zA-Z0-9_]{2}$"
                        fragment_length = 2
                        fragment_default = "01"
                        use_part_number = True
                    else:
                        regex = "^(.*?)-[a-zA-Z0-9_]{5}$"
                        fragment_length = 5
                        fragment_default = "20001"
                        use_part_number = True
                else:
                    # Basic default serial number pattern (1,2,3,... etc.)
                    regex = "^(.*?)"
                    fragment_length = False
                    fragment_default = "1"
                    use_part_number = False

                inventory_qs = Inventory.objects.filter(part=part_obj).filter(
                    serial_number__iregex=regex
                )
                if inventory_qs:
                    inventory_last = inventory_qs.latest("id")
                    last_serial_number_fragment = int(
                        inventory_last.serial_number.split("-")[-1]
                    )
                    new_serial_number_fragment = last_serial_number_fragment + 1
                    # Fill fragment with leading zeroes if necessary
                    if fragment_length:
                        new_serial_number_fragment = str(
                            new_serial_number_fragment
                        ).zfill(fragment_length)
                else:
                    new_serial_number_fragment = fragment_default

                if use_part_number:
                    new_serial_number = (
                        part_obj.part_number + "-" + str(new_serial_number_fragment)
                    )
                else:
                    new_serial_number = str(new_serial_number_fragment)

    data = {
        "new_serial_number": new_serial_number,
    }
    return JsonResponse(data)


# Function to search subassembly options by serial number, load object
def load_subassemblies_by_serialnumber(request):
    serial_number = request.GET.get("serial_number").strip()
    parent_id = request.GET.get("parent_id")

    parent = Inventory.objects.get(id=parent_id)
    inventory_items = Inventory.objects.filter(serial_number__icontains=serial_number)
    return render(
        request,
        "inventory/available_subassemblies.html",
        {
            "inventory_items": inventory_items,
            "parent": parent,
        },
    )


# Function to search Build subassembly options by serial number, load object
def load_build_subassemblies_by_serialnumber(request):
    serial_number = request.GET.get("serial_number").strip()
    parent_id = request.GET.get("parent_id")
    assemblypart_id = request.GET.get("assemblypart_id")
    build_id = request.GET.get("build_id")

    if parent_id:
        parent = Inventory.objects.get(id=parent_id)
    else:
        parent = None
    assembly_part = AssemblyPart.objects.get(id=assemblypart_id)
    build = Build.objects.get(id=build_id)
    inventory_items = (
        Inventory.objects.filter(serial_number__icontains=serial_number)
        .filter(part=assembly_part.part)
        .filter(build__isnull=True)
        .filter(parent__isnull=True)
    )
    return render(
        request,
        "inventory/available_build_subassemblies.html",
        {
            "inventory_items": inventory_items,
            "parent": parent,
            "assembly_part": assembly_part,
            "build": build,
        },
    )


# Function to search destination assignment subassembly options by serial number, load object
def load_destination_subassemblies_by_serialnumber(request):
    serial_number = request.GET.get("serial_number").strip()
    parent_id = request.GET.get("parent_id")
    assemblypart_id = request.GET.get("assemblypart_id")
    location_id = request.GET.get("location_id")

    assembly_part = AssemblyPart.objects.get(id=assemblypart_id)
    parent = Inventory.objects.get(id=parent_id)
    location = Location.objects.get(id=location_id)
    inventory_items = (
        Inventory.objects.filter(serial_number__icontains=serial_number)
        .filter(part=assembly_part.part)
        .filter(build__isnull=True)
        .filter(parent__isnull=True)
    )
    return render(
        request,
        "inventory/available_destination_subassemblies.html",
        {
            "inventory_items": inventory_items,
            "parent": parent,
            "assembly_part": assembly_part,
            "location": location,
        },
    )


# Inventory CBV Views for CRUD operations and menu Actions
# ------------------------------------------------------------------------------
# AJAX Views


class InventoryAjaxDetailView(LoginRequiredMixin, DetailView):
    model = Inventory
    context_object_name = "inventory_item"
    template_name = "inventory/ajax_inventory_detail.html"
    queryset = (
        Inventory.objects.prefetch_related("actions__user")
        .prefetch_related("actions__location")
        .prefetch_related("actions__photos")
        .prefetch_related("photos")
        .prefetch_related("inventory_deployments")
        .select_related(
            "location", "parent", "revision__part", "build", "part", "assembly_part"
        )
    )

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxDetailView, self).get_context_data(**kwargs)
        # Get Printers to display in print dropdown
        printers = Printer.objects.all()
        # Get this item's custom fields with most recent Values
        if self.object.fieldvalues.exists():
            custom_fields = self.object.fieldvalues.filter(is_current=True)
        else:
            custom_fields = None

        if self.object.calibration_events.exists():
            coeff_events = self.object.calibration_events.prefetch_related(
                "coefficient_value_sets__coefficient_values"
            )
        else:
            coeff_events = None

        part_has_configs = False
        part_has_consts = False
        if self.object.part.config_name_events.exists():
            if (
                self.object.part.config_name_events.first()
                .config_names.filter(config_type="conf")
                .exists()
            ):
                part_has_configs = True
            if (
                self.object.part.config_name_events.first()
                .config_names.filter(config_type="cnst")
                .exists()
            ):
                part_has_consts = True

        # Get Inventory items by Root Locations
        inventory_location_data = []
        root_locations = Location.objects.root_nodes().exclude(root_type="Trash")
        for root in root_locations:
            locations_list = root.get_descendants(include_self=True).values_list(
                "id", flat=True
            )
            items = self.object.part.inventory.filter(location__in=locations_list)
            if items:
                data = {
                    "location_root": root,
                    "inventory_items": items,
                }
                inventory_location_data.append(data)

        context.update(
            {
                "part_has_configs": part_has_configs,
                "part_has_consts": part_has_consts,
                "coeff_events": coeff_events,
                "printers": printers,
                "custom_fields": custom_fields,
                "node_type": node_type,
                "inventory_location_data": inventory_location_data,
            }
        )
        return context


class InventoryAjaxSnapshotDetailView(LoginRequiredMixin, DetailView):
    model = Inventory
    context_object_name = "inventory_item"
    template_name = "inventory/ajax_inventory_snapshot_detail.html"


class InventoryAjaxCreateBasicView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Inventory
    form_class = InventoryAddForm
    context_object_name = "inventory_item"
    template_name = "inventory/ajax_inventory_form.html"

    def get_success_url(self):
        return reverse("inventory:ajax_inventory_detail", args=(self.object.id,))

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxCreateBasicView, self).get_context_data(**kwargs)
        # Add Parts list to context to build form filter
        context.update({"part_types": PartType.objects.all()})
        if "parent_pk" in self.kwargs:
            context.update(
                {"parent": Inventory.objects.get(id=self.kwargs["parent_pk"])}
            )
        return context

    def get_form_kwargs(self):
        kwargs = super(InventoryAjaxCreateBasicView, self).get_form_kwargs()
        if "parent_pk" in self.kwargs:
            kwargs["parent_pk"] = self.kwargs["parent_pk"]
        if "current_location" in self.kwargs:
            kwargs["current_location"] = self.kwargs["current_location"]
        return kwargs

    def get_initial(self):
        # Returns the initial data to use for forms on this view.
        initial = super(InventoryAjaxCreateBasicView, self).get_initial()
        if "parent_pk" in self.kwargs:
            parent = Inventory.objects.get(id=self.kwargs["parent_pk"])
            part_templates = Part.objects.get(id=parent.part.id)
            if parent.deployment:
                initial["deployment"] = parent.deployment.id
            initial["parent"] = self.kwargs["parent_pk"]
            initial["location"] = self.kwargs["current_location"]
            initial["part"] = part_templates
        elif "current_location" in self.kwargs:
            initial["location"] = self.kwargs["current_location"]
        return initial

    def form_valid(self, form):
        self.object = form.save()
        # Call the function to create an Action history chain this event
        _create_action_history(self.object, Action.ADD, self.request.user)
        # Check if this Part has Custom fields with global default values, create fields if needed
        try:
            # Exclude any fields with Global Part Values
            custom_fields = self.object.part.user_defined_fields.exclude(
                fieldvalues__part=self.object.part
            )
        except Field.DoesNotExist:
            custom_fields = None

        if custom_fields:
            for field in custom_fields:
                if field.field_default_value:
                    # create new value object
                    fieldvalue = FieldValue.objects.create(
                        field=field,
                        field_value=field.field_default_value,
                        inventory=self.object,
                        is_current=True,
                        is_default_value=True,
                    )

        # Check if this Part has Custom fields with Part Template default levels, create fields if needed
        try:
            # Only fields with Default Part Values
            custom_fields = (
                self.object.part.user_defined_fields.filter(
                    fieldvalues__part=self.object.part
                )
                .filter(fieldvalues__is_current=True)
                .distinct()
            )
        except Field.DoesNotExist:
            custom_fields = None

        if custom_fields:
            for field in custom_fields:
                # Check if this Part has Custom fields with Part Template default levels, create fields if needed
                try:
                    default_value = field.fieldvalues.filter(
                        part=self.object.part
                    ).latest()
                except FieldValue.DoesNotExist:
                    default_value = None

                if default_value:
                    fieldvalue = FieldValue.objects.create(
                        field=field,
                        field_value=default_value.field_value,
                        inventory=self.object,
                        is_current=True,
                        user=default_value.user,
                    )

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.id,
                "object_type": self.object.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response


class InventoryAjaxUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = Inventory
    form_class = InventoryForm
    context_object_name = "inventory_item"
    template_name = "inventory/ajax_inventory_form.html"

    def form_valid(self, form):
        self.object = form.save()

        # Check is this Part has custom fields
        if self.object.part.user_defined_fields.exists():
            # loop through all cleaned_data fields, get custom fields, update the FieldValue model
            for key, value in form.cleaned_data.items():
                # check for the 'udffield' key in string, if so proceed
                field_keys = key.partition("_")

                if field_keys[0] == "udffield":
                    field_id = int(field_keys[2])
                    # Check if this inventory object has value for this field
                    try:
                        currentvalue = self.object.fieldvalues.filter(
                            field_id=field_id
                        ).latest()
                    except FieldValue.DoesNotExist:
                        currentvalue = None

                    # If current value is different than new value, update is_current, add new value, add Action to History
                    if currentvalue:
                        if (
                            currentvalue.field_value != str(value)
                            and currentvalue.field_value != value
                        ):
                            currentvalue.is_current = False
                            currentvalue.save()
                            # Create new value object
                            new_fieldvalue = FieldValue.objects.create(
                                field_id=field_id,
                                field_value=value,
                                inventory=self.object,
                                is_current=True,
                                user=self.request.user,
                            )
                            # Create action record for history
                            # Check if UDF field is a DateField, if so format date for display
                            if new_fieldvalue.field.field_type == "DateField":
                                try:
                                    value = value.strftime("%m-%d-%Y %H:%M:%S")
                                except:
                                    pass

                            self.object.detail = 'Change field value for "%s" to %s' % (
                                currentvalue.field,
                                value,
                            )
                            self.object.save()
                            # Call the function to create an Action history chain this event
                            _create_action_history(
                                self.object, Action.FIELDCHANGE, self.request.user
                            )
                    else:
                        if value:
                            # Create new value object
                            fieldvalue = FieldValue.objects.create(
                                field_id=field_id,
                                field_value=value,
                                inventory=self.object,
                                is_current=True,
                                user=self.request.user,
                            )
                            # Create action record for history
                            # Check if UDF field is a DateField, if so format date for display
                            if fieldvalue.field.field_type == "DateField":
                                try:
                                    value = value.strftime("%m-%d-%Y %H:%M:%S")
                                except:
                                    pass

                            self.object.detail = (
                                'Add initial field value for "%s" to %s'
                                % (fieldvalue.field, value)
                            )
                            self.object.save()
                            # Call the function to create an Action history chain this event
                            _create_action_history(
                                self.object, Action.FIELDCHANGE, self.request.user
                            )

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.id,
                "object_type": self.object.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse("inventory:ajax_inventory_detail", args=(self.object.id,))


class InventoryAjaxActionView(InventoryAjaxUpdateView):
    def get_form_class(self):
        ACTION_FORMS = {
            "locationchange": ActionLocationChangeForm,
            "subchange": ActionSubassemblyChangeForm,
            "removefrombuild": ActionRemoveFromBuildForm,
            "deploymentrecover": ActionRecoverFromDeploymentForm,
            "removedest": ActionRemoveDestinationForm,
            "test": ActionTestForm,
            "note": ActionNoteForm,
            "flag": ActionFlagForm,
            "movetotrash": ActionMoveToTrashForm,
        }
        action_type = self.kwargs["action_type"]
        form_class_name = ACTION_FORMS[action_type]

        return form_class_name

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxActionView, self).get_context_data(**kwargs)
        # Get latest detail information if part is flagged
        if (
            Action.objects.filter(
                Q(action_type="flag") & Q(inventory_id=self.object.id)
            ).exists()
            and self.kwargs["action_type"] == "flag"
        ):
            context.update(
                {
                    "latest_flag": Action.objects.filter(
                        Q(action_type="flag") & Q(inventory_id=self.object.id)
                    ).latest("created_at")
                }
            )
        if "action_type" in self.kwargs:
            context["action_type"] = self.kwargs["action_type"]
        else:
            context["action_type"] = None

        return context

    def form_valid(self, form):
        action_type = self.kwargs["action_type"]
        detail = self.object.detail
        created_at = form.cleaned_data.get("date", timezone.now())
        cruise = None

        inventory_form = form.save()

        if action_type == Action.LOCATIONCHANGE or action_type == Action.MOVETOTRASH:
            # Get any subassembly children items, move their location sto match parent and add Action to history
            subassemblies = self.object.get_descendants()
            assembly_parts_added = []
            for item in subassemblies:
                if self.object.assembly_part:
                    sub_assembly_parts = self.object.assembly_part.get_descendants()
                    sub_assembly_part = sub_assembly_parts.filter(part=item.part)
                    for sub in sub_assembly_part:
                        if sub.id not in assembly_parts_added:
                            item.assembly_part = sub
                            assembly_parts_added.append(sub.id)
                            break
                else:
                    item.assembly_part = None

                # If "movetotrash", need to remove all Build/AssemblyPart/Destination data for children
                if action_type == Action.MOVETOTRASH:
                    item.build = None
                    item.assembly_part = None
                    item.assigned_destination_root = None
                item.location = self.object.location
                item.save()
                # Call the function to create an Action history chain for this event
                _create_action_history(
                    item, action_type, self.request.user, self.object
                )
                # item.create_action_record(self.request.user, action_type, detail)

            # If "movetotrash", need to remove all Build/AssemblyPart/Destination data
            if action_type == Action.MOVETOTRASH:
                self.object.build = None
                self.object.assembly_part = None
                self.object.assigned_destination_root = None
                self.object.save()

        if action_type == Action.REMOVEFROMBUILD:
            # Get any subassembly children items, add self for full queryset
            subassemblies = self.object.get_descendants()
            for item in subassemblies:
                item.assembly_part = None
                item.build = None
                item.location = self.object.location
                item.save()
                # item.detail = ' Removed from'
                # Call the function to create an Action history chain for all child items
                _create_action_history(
                    item, action_type, self.request.user, self.object
                )

        if action_type == Action.DEPLOYMENTRECOVER:
            cruise = form.cleaned_data["cruise"]
            action_date = form.cleaned_data["date"]

            inventory_deployment = (
                self.object.inventory_deployments.get_active_deployment()
            )
            inventory_deployment.cruise_recovered = cruise
            inventory_deployment.deployment_recovery_date = action_date
            inventory_deployment.save()

            # Find Build it was removed from
            old_build = self.object.get_latest_build()
            if old_build:
                # Create Build Action record
                _create_action_history(
                    old_build,
                    Action.SUBCHANGE,
                    self.request.user,
                    self.object,
                    "",
                    action_date,
                )

            # Get any subassembly children items, add Action to history
            subassemblies = self.object.get_descendants()
            for item in subassemblies:
                item.assembly_part = None
                item.build = None
                item.location = self.object.location
                item.save()
                inventory_deployment = (
                    item.inventory_deployments.get_active_deployment()
                )
                inventory_deployment.cruise_recovered = cruise
                inventory_deployment.deployment_recovery_date = action_date
                inventory_deployment.save()
                # Call the function to create an Action history chain for all child items
                _create_action_history(
                    item, action_type, self.request.user, self.object, "", action_date
                )
                # Create Build Action record
                _create_action_history(
                    old_build,
                    Action.SUBCHANGE,
                    self.request.user,
                    item,
                    "",
                    action_date,
                )

        if action_type == Action.REMOVEDEST:
            # Get any subassembly children items, add Action to history
            subassemblies = self.object.get_descendants()
            for item in subassemblies:
                item.assembly_part = None
                item.assigned_destination_root = None
                item.save()
                # Call the function to create an Action history chain for all child items
                _create_action_history(
                    item, action_type, self.request.user, self.object
                )

        if action_type == Action.SUBCHANGE:
            # Get any subassembly children items, move their location to match parent and add Action to history
            subassemblies = self.object.get_descendants()
            assembly_parts_added = []
            for item in subassemblies:
                if self.object.assembly_part:
                    sub_assembly_parts = self.object.assembly_part.get_descendants()
                    sub_assembly_part = sub_assembly_parts.filter(part=item.part)
                    for sub in sub_assembly_part:
                        if sub.id not in assembly_parts_added:
                            item.assembly_part = sub
                            assembly_parts_added.append(sub.id)
                            break
                else:
                    item.assembly_part = None

                item.location = self.object.location
                item.build = self.object.build
                item.assigned_destination_root = self.object.assigned_destination_root
                item.detail = "Parent Inventory Change"
                item.save()
                # Call the function to create an Action history chain for all child items
                _create_action_history(
                    item, action_type, self.request.user, self.object
                )

        # Call the function to create an Action history chain for this event
        _create_action_history(
            self.object, action_type, self.request.user, "", "", created_at
        )
        # action_record = self.object.create_action_record(self.request.user, action_type, detail, created_at, cruise, 'inventory_deployment')

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.id,
                "object_type": self.object.get_object_type(),
                "detail_path": self.get_success_url(),
                "location_id": self.object.location.id,
            }
            return JsonResponse(data)
        else:
            return response


class ActionNoteAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Action
    form_class = ActionPhotoNoteForm
    context_object_name = "action"
    template_name = "inventory/ajax_inventory_photo_note_form.html"

    def get_context_data(self, **kwargs):
        context = super(ActionNoteAjaxCreateView, self).get_context_data(**kwargs)
        inventory_item = Inventory.objects.get(id=self.kwargs["pk"])
        context.update({"inventory_item": inventory_item})
        return context

    def get_initial(self):
        inventory_item = Inventory.objects.get(id=self.kwargs["pk"])
        return {"inventory": inventory_item.id, "location": inventory_item.location_id}

    def form_valid(self, form):
        inventory_item = Inventory.objects.get(id=self.kwargs["pk"])
        self.object = form.save()
        self.object.user_id = self.request.user.id
        self.object.action_type = "note"
        self.object.object_type = "inventory"
        self.object.parent = inventory_item.parent
        self.object.build = inventory_item.build
        self.object.deployment = inventory_item.get_latest_deployment()
        self.object.save()

        photo_ids = form.cleaned_data["photo_ids"]
        if photo_ids:
            photo_ids = photo_ids.split(",")
            for id in photo_ids:
                photo = PhotoNote.objects.get(id=id)
                photo.action_id = self.object.id
                photo.save()

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.inventory_id,
                "object_type": self.object.inventory.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse(
            "inventory:ajax_inventory_detail", args=(self.object.inventory_id,)
        )


class ActionPhotoUploadAjaxCreateView(View):
    def get(self, request, **kwargs):
        inventory_item = Inventory.objects.get(id=self.kwargs["pk"])
        form = ActionPhotoUploadForm()
        return render(
            self.request,
            "inventory/ajax_inventory_photo_note_form.html",
            {
                "inventory_item": inventory_item,
            },
        )

    def post(self, request, **kwargs):
        form = ActionPhotoUploadForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            photo_note = form.save()
            photo_note.inventory_id = self.kwargs["pk"]
            photo_note.user_id = self.request.user.id
            photo_note.save()
            data = {
                "is_valid": True,
                "name": photo_note.photo.name,
                "url": photo_note.photo.url,
                "photo_id": photo_note.id,
                "file_type": photo_note.file_type(),
            }
        else:
            data = {
                "is_valid": False,
                "errors": form.errors,
            }
        return JsonResponse(data)


class ActionHistoryNoteAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Action
    form_class = ActionHistoryNoteForm
    context_object_name = "action"
    template_name = "inventory/ajax_inventory_form.html"

    def get_context_data(self, **kwargs):
        context = super(ActionHistoryNoteAjaxCreateView, self).get_context_data(
            **kwargs
        )
        inventory_item = Inventory.objects.get(id=self.kwargs["pk"])
        context.update({"inventory_item": inventory_item})
        return context

    def get_initial(self):
        return {"inventory": self.kwargs["pk"]}

    def form_valid(self, form):
        self.object = form.save()
        self.object.user_id = self.request.user.id
        self.object.action_type = "historynote"
        self.object.object_type = "inventory"
        self.object.save()

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.inventory_id,
                "object_type": self.object.inventory.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse(
            "inventory:ajax_inventory_detail", args=(self.object.inventory_id,)
        )


class InventoryAjaxAddToBuildListView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/ajax_inventory_add_to_build.html"

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxAddToBuildListView, self).get_context_data(
            **kwargs
        )
        inventory_item = Inventory.objects.get(id=self.kwargs["pk"])
        builds = Build.objects.all().order_by("location__name")

        if inventory_item.assembly_part:
            for build in builds:
                for assembly_part in build.assembly_revision.assembly_parts.all():
                    if assembly_part != inventory_item.assembly_part:
                        x = False
                    else:
                        x = True
                        break
                if not x:
                    builds = builds.exclude(id=build.id)
        else:
            for build in builds:
                for assembly_part in build.assembly_revision.assembly_parts.all():
                    if assembly_part.part != inventory_item.part:
                        x = False
                    else:
                        x = True
                        break
                if not x:
                    builds = builds.exclude(id=build.id)

        builds = builds.prefetch_related("assembly_revision__assembly_parts")

        if inventory_item.assembly_part:
            assembly_parts = AssemblyPart.objects.filter(
                id=inventory_item.assembly_part.id
            )
        else:
            assembly_parts = (
                AssemblyPart.objects.filter(part=inventory_item.part)
                .filter(assembly_revision__builds__in=builds)
                .select_related()
                .distinct()
            )

        context.update({"inventory_item": inventory_item})
        context.update({"assembly_parts": assembly_parts})
        context.update({"builds": builds})
        return context


class InventoryAjaxAddToBuildActionView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        action_type = Action.ADDTOBUILD
        assembly_part = AssemblyPart.objects.get(id=self.kwargs["assembly_part_pk"])
        inventory_item = Inventory.objects.get(id=self.kwargs["pk"])
        build = Build.objects.get(id=self.kwargs["build_pk"])

        if assembly_part.parent:
            try:
                parent = (
                    Inventory.objects.filter(assembly_part=assembly_part.parent)
                    .filter(build=build)
                    .first()
                )
            except Inventory.DoesNotExist:
                parent = None
        else:
            parent = None

        if build.is_deployed_to_field():
            # Need to save temporary object data for extra Deployment to Field form step
            self.request.session["inventory_todeploy"] = {}
            self.request.session["inventory_todeploy"]["id"] = inventory_item.id
            self.request.session["inventory_todeploy"][
                "location_id"
            ] = build.location.id
            self.request.session["inventory_todeploy"]["build_id"] = build.id
            self.request.session["inventory_todeploy"][
                "assembly_part_id"
            ] = assembly_part.id
            if parent:
                self.request.session["inventory_todeploy"]["parent_id"] = parent.id
            self.request.session.modified = True
            print(self.request.session["inventory_todeploy"])
            return reverse("inventory:ajax_deploy_action", args=(self.kwargs["pk"],))
        else:
            inventory_item.assembly_part = assembly_part
            inventory_item.build = build
            inventory_item.parent = parent
            inventory_item.location = build.location
            inventory_item.save()
            # Call the function to create an Action history chain
            _create_action_history(inventory_item, action_type, self.request.user)

            # Get any subassembly children items, move their location to match parent and add Action to history
            subassemblies = inventory_item.get_descendants()
            assembly_parts_added = []
            for item in subassemblies:
                sub_assembly_parts = inventory_item.assembly_part.get_descendants()
                sub_assembly_part = sub_assembly_parts.filter(part=item.part)

                for sub in sub_assembly_part:
                    if sub.id not in assembly_parts_added:
                        item.assembly_part = sub
                        assembly_parts_added.append(sub.id)
                        break

                item.location = inventory_item.location
                item.build = inventory_item.build
                item.save()
                # Call the function to create an Action history chain for child items
                _create_action_history(
                    item, action_type, self.request.user, inventory_item
                )

            # Check if any subassembly orphan children items already exist.  If so, make this item the parent
            children = inventory_item.assembly_part.get_children()
            for child in children:
                if child.inventory.exists():
                    child_item = Inventory.objects.filter(assembly_part=child).filter(
                        build=subassembly.build
                    )
                    for c in child_item:
                        if c.build == inventory_item.build:
                            c.parent = inventory_item
                            c.save()

        return reverse("inventory:ajax_inventory_detail", args=(self.kwargs["pk"],))


class InventoryAjaxByAssemblyPartListView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/ajax_inventory_assemblypart_add_subassembly.html"

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxByAssemblyPartListView, self).get_context_data(
            **kwargs
        )
        assembly_part = AssemblyPart.objects.get(id=self.kwargs["pk"])
        location = Location.objects.get(id=self.kwargs["location_pk"])
        build = Build.objects.get(id=self.kwargs["build_pk"])
        if assembly_part.parent:
            try:
                parent = (
                    Inventory.objects.filter(assembly_part=assembly_part.parent)
                    .filter(build=build)
                    .first()
                )
            except Inventory.DoesNotExist:
                parent = None
        else:
            parent = None
        inventory_items = (
            Inventory.objects.filter(part=assembly_part.part)
            .filter(build__isnull=True)
            .filter(parent__isnull=True)
            .exclude(location__root_type="Trash")
        )
        inventory_items = inventory_items.filter(
            Q(assembly_part=assembly_part) | Q(assembly_part__isnull=True)
        )

        context.update({"inventory_items": inventory_items})
        context.update({"assembly_part": assembly_part})
        context.update({"parent": parent})
        context.update({"location": location})
        context.update({"build": build})

        return context


class InventoryAjaxByAssemblyPartActionView(LoginRequiredMixin, RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        action_type = Action.ADDTOBUILD
        subassembly = Inventory.objects.get(id=self.kwargs["pk"])
        assembly_part = AssemblyPart.objects.get(id=self.kwargs["assembly_part_pk"])
        build = Build.objects.get(id=self.kwargs["build_pk"])
        location = build.location
        if "parent_pk" in self.kwargs:
            parent = Inventory.objects.get(id=self.kwargs["parent_pk"])
        else:
            parent = None

        if build.is_deployed_to_field():
            # Need to save temporary object data for extra Deployment form step
            self.request.session["inventory_todeploy"] = {}
            self.request.session["inventory_todeploy"]["id"] = subassembly.id
            self.request.session["inventory_todeploy"]["location_id"] = location.id
            self.request.session["inventory_todeploy"]["build_id"] = build.id
            self.request.session["inventory_todeploy"][
                "assembly_part_id"
            ] = assembly_part.id
            if parent:
                self.request.session["inventory_todeploy"]["parent_id"] = parent.id
            self.request.session.modified = True
            print(self.request.session["inventory_todeploy"])
            return reverse("inventory:ajax_deploy_action", args=(self.kwargs["pk"],))
        else:
            subassembly.location = location
            subassembly.build = build
            subassembly.future_destination = None
            subassembly.parent = parent
            subassembly.assembly_part = assembly_part
            subassembly.save()

            # Get any subassembly children items, move their location to match parent and add Action to history
            subassemblies = subassembly.get_descendants()
            assembly_parts_added = []
            for item in subassemblies:
                sub_assembly_parts = subassembly.assembly_part.get_descendants()
                sub_assembly_part = sub_assembly_parts.filter(part=item.part)

                for sub in sub_assembly_part:
                    if sub.id not in assembly_parts_added:
                        item.assembly_part = sub
                        assembly_parts_added.append(sub.id)
                        break

                item.location = subassembly.location
                item.build = subassembly.build
                # item.detail = 'Moved to %s' % (item.build)
                item.save()
                # Call the function to create an Action history chain for this event
                _create_action_history(
                    item, action_type, self.request.user, subassembly
                )
            # Call the function to create an Action history chain for this event
            _create_action_history(subassembly, action_type, self.request.user)

            # Check if any subassembly orphan children items already exist.  If so, make this item the parent
            children = subassembly.assembly_part.get_children()
            for child in children:
                if child.inventory.exists():
                    child_item = Inventory.objects.filter(assembly_part=child).filter(
                        build=subassembly.build
                    )
                    for c in child_item:
                        if c.build == subassembly.build:
                            c.parent = subassembly
                            c.save()

        return reverse("inventory:ajax_inventory_detail", args=(self.kwargs["pk"],))


class ActionDeployInventoryAjaxFormView(LoginRequiredMixin, AjaxFormMixin, FormView):
    form_class = ActionDeployInventoryForm
    context_object_name = "action"
    template_name = "inventory/ajax_inventory_form.html"

    def get_context_data(self, **kwargs):
        context = super(ActionDeployInventoryAjaxFormView, self).get_context_data(
            **kwargs
        )
        inventory_item = Inventory.objects.get(id=self.kwargs["pk"])

        context.update(
            {
                "inventory_item": inventory_item,
                "action_type": Action.DEPLOYMENTTOFIELD,
            }
        )
        return context

    def get_initial(self):
        return {"inventory": self.kwargs["pk"]}

    def form_valid(self, form):
        inventory_item = Inventory.objects.get(id=self.kwargs["pk"])
        cruise = form.cleaned_data["cruise"]
        action_date = form.cleaned_data["date"]
        action_type = Action.ADDTOBUILD

        # Retrieve temporary object data from session key, update Inventory object
        inventory_todeploy = self.request.session.get("inventory_todeploy")
        inventory_item.location_id = inventory_todeploy["location_id"]
        inventory_item.build_id = inventory_todeploy["build_id"]
        inventory_item.future_destination = None
        inventory_item.parent_id = inventory_todeploy.get("parent_id", None)
        inventory_item.assembly_part_id = inventory_todeploy["assembly_part_id"]
        inventory_item.save()

        # Get any subassembly children items, move their location to match parent and add Action to history
        subassemblies = inventory_item.get_descendants()
        assembly_parts_added = []
        for item in subassemblies:
            sub_assembly_parts = inventory_item.assembly_part.get_descendants()
            sub_assembly_part = sub_assembly_parts.filter(part=item.part)

            for sub in sub_assembly_part:
                if sub.id not in assembly_parts_added:
                    item.assembly_part = sub
                    assembly_parts_added.append(sub.id)
                    break

            item.location = inventory_item.location
            item.build = inventory_item.build
            # item.detail = 'Moved to %s' % (item.build)
            item.save()
            # Call the function to create an Action history chain for this event
            _create_action_history(
                item, action_type, self.request.user, inventory_item, "", action_date
            )
        # Call the function to create an Action history chain for the ADDTOBUILD event
        _create_action_history(
            inventory_item, action_type, self.request.user, None, "", action_date
        )

        # Add DEPLOYMENTTOFIELD Actions for all Inventory item and children
        inventory_tree = inventory_item.get_descendants(include_self=True)
        for item in inventory_tree:
            # Update InventoryDeployment object
            inventory_deployment = item.inventory_deployments.get_active_deployment()
            inventory_deployment.cruise_deployed = cruise
            inventory_deployment.deployment_to_field_date = action_date
            inventory_deployment.save()
            # Call the function to create an Action history chain for this event
            _create_action_history(
                item, Action.DEPLOYMENTTOFIELD, self.request.user, None, "", action_date
            )

        # Check if any subassembly orphan children items already exist.  If so, make this item the parent
        children = inventory_item.assembly_part.get_children()
        for child in children:
            if child.inventory.exists():
                child_item = Inventory.objects.filter(assembly_part=child).filter(
                    build=inventory_item.build
                )
                for c in child_item:
                    if c.build == inventory_item.build:
                        c.parent = inventory_item
                        c.save()

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                "message": "Successfully submitted form data.",
                "object_id": inventory_item.id,
                "object_type": inventory_item.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse("inventory:ajax_inventory_detail", args=(self.kwargs["pk"],))


class InventoryAjaxAssignDestinationView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/ajax_inventory_assign_destination.html"

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxAssignDestinationView, self).get_context_data(
            **kwargs
        )
        inventory_item = Inventory.objects.get(id=self.kwargs["pk"])
        assembly_parts = (
            AssemblyPart.objects.filter(part=inventory_item.part)
            .order_by("assembly_revision")
            .select_related()
        )

        context.update({"inventory_item": inventory_item})
        context.update({"assembly_parts": assembly_parts})
        return context


class InventoryAjaxAssignDestinationActionView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        assembly_part = AssemblyPart.objects.get(id=self.kwargs["assembly_part_pk"])
        inventory_item = Inventory.objects.get(id=self.kwargs["pk"])

        inventory_item.assembly_part = assembly_part
        inventory_item.assigned_destination_root = inventory_item
        inventory_item.save()
        # Call the function to create an Action history chain for this event
        _create_action_history(inventory_item, Action.ASSIGNDEST, self.request.user)

        # Get any subassembly children items, move their Assembly Part assignment to match parent
        subassemblies = inventory_item.get_descendants()
        assembly_parts_added = []
        for item in subassemblies:
            item.assigned_destination_root = inventory_item
            sub_assembly_parts = inventory_item.assembly_part.get_descendants()
            sub_assembly_part = sub_assembly_parts.filter(part=item.part)
            for sub in sub_assembly_part:
                if sub.id not in assembly_parts_added:
                    item.assembly_part = sub
                    assembly_parts_added.append(sub.id)
                    break
            item.save()
            # Call the function to create an Action history chain for this event
            _create_action_history(
                item, Action.ASSIGNDEST, self.request.user, inventory_item
            )

        return reverse("inventory:ajax_inventory_detail", args=(self.kwargs["pk"],))


class InventoryAjaxDestinationSubassemblyListView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/ajax_inventory_destination_add_subassembly.html"

    def get_context_data(self, **kwargs):
        context = super(
            InventoryAjaxDestinationSubassemblyListView, self
        ).get_context_data(**kwargs)
        navtree_node_id = self.request.GET.get("navTreeNodeID")
        assembly_part = AssemblyPart.objects.get(id=self.kwargs["pk"])
        location = Location.objects.get(id=self.kwargs["location_pk"])
        assigned_destination_root = Inventory.objects.get(
            id=self.kwargs["assigned_destination_root_pk"]
        )

        if assembly_part.parent:
            try:
                parent = (
                    Inventory.objects.filter(assembly_part=assembly_part.parent)
                    .filter(build__isnull=True)
                    .first()
                )
            except Inventory.DoesNotExist:
                parent = None
        else:
            parent = None
        inventory_items = (
            Inventory.objects.filter(part=assembly_part.part)
            .filter(build__isnull=True)
            .filter(parent__isnull=True)
            .filter(assigned_destination_root__isnull=True)
            .exclude(location__root_type="Trash")
        )

        context.update(
            {
                "inventory_items": inventory_items,
                "navtree_node_id": navtree_node_id,
                "assembly_part": assembly_part,
                "parent": parent,
                "location": location,
                "assigned_destination_root": assigned_destination_root,
            }
        )
        return context


class InventoryAjaxDestinationSubassemblyActionView(LoginRequiredMixin, RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        subassembly = Inventory.objects.get(id=self.kwargs["pk"])
        assembly_part = AssemblyPart.objects.get(id=self.kwargs["assembly_part_pk"])
        location = Location.objects.get(id=self.kwargs["location_pk"])
        assigned_destination_root = Inventory.objects.get(
            id=self.kwargs["assigned_destination_root_pk"]
        )

        if "parent_pk" in self.kwargs:
            parent = Inventory.objects.get(id=self.kwargs["parent_pk"])
        else:
            parent = None

        subassembly.location = location
        subassembly.assembly_part = assembly_part
        subassembly.parent = parent
        subassembly.assigned_destination_root = assigned_destination_root
        subassembly.save()

        detail = "Destination assigned - %s." % (subassembly.assembly_part.assembly)
        # Find previous location to add to Detail field text
        old_location_pk = subassembly.tracker.previous("location")
        if old_location_pk != subassembly.location:
            detail = " Moved to %s." % (subassembly.location)
        if subassembly.parent:
            detail = detail + " Added to %s" % (subassembly.parent)
            parent_record = Action.objects.create(
                action_type="subchange",
                detail="Subassembly %s added." % (subassembly),
                location=subassembly.location,
                user=self.request.user,
                inventory=subassembly.parent,
            )
        action_record = Action.objects.create(
            action_type="invchange",
            detail=detail,
            location=subassembly.location,
            user=self.request.user,
            inventory=subassembly,
        )

        # Check if any subassembly orphan children items already exist.  If so, make this item the parent
        children = subassembly.assembly_part.get_children()
        for child in children:
            if child.inventory.exists():
                child_item = Inventory.objects.filter(assembly_part=child).filter(
                    assigned_destination_root=subassembly.assigned_destination_root
                )
                for c in child_item:
                    if (
                        c.assigned_destination_root
                        == subassembly.assigned_destination_root
                    ):
                        c.parent = subassembly
                        c.save()

        # Get any subassembly children items, move their location to match parent and add Action to history
        subassemblies = subassembly.get_descendants()
        assembly_parts_added = []
        for item in subassemblies:
            sub_assembly_parts = subassembly.assembly_part.get_descendants()
            sub_assembly_part = sub_assembly_parts.filter(part=item.part)

            for sub in sub_assembly_part:
                if sub.id not in assembly_parts_added:
                    item.assembly_part = sub
                    assembly_parts_added.append(sub.id)
                    break

            item.location = subassembly.location
            item.build = subassembly.build
            item.assigned_destination_root = subassembly.assigned_destination_root

            if item.build:
                item.detail = "Moved to %s" % (item.build)
            else:
                item.detail = "Parent Inventory Change"

            item.save()
            action_record = Action.objects.create(
                action_type="invchange",
                detail=item.detail,
                location=item.location,
                user=self.request.user,
                inventory=item,
            )

        return reverse("inventory:ajax_inventory_detail", args=(self.kwargs["pk"],))


class InventoryAjaxParentListView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/ajax_inventory_add_to_parent.html"

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxParentListView, self).get_context_data(**kwargs)
        item = Inventory.objects.get(id=self.kwargs["pk"])
        items_with_assembly_part = Inventory.objects.filter(part=item.part).filter(
            assembly_part__isnull=False
        )

        assembly_parts = AssemblyPart.objects.filter(part=item.part)
        assembly_parts_list = []
        for ap in assembly_parts:
            parent = AssemblyPart.objects.get(id=ap.id).get_ancestors().last()
            assembly_parts_list.append(parent)
        part_templates = Part.objects.filter(assembly_parts__in=assembly_parts_list)
        parent_items = (
            Inventory.objects.filter(part__in=part_templates)
            .filter(build__isnull=True)
            .exclude(location__root_type="Trash")
            .order_by("part__name")
        )

        for parent in parent_items:
            # Check if the assembly part template spot is already filled, remove parent from queryset
            children = parent.get_children()
            if children:
                for child in children:
                    if child in items_with_assembly_part:
                        parent_items = parent_items.exclude(id=parent.id)

        for parent in parent_items:
            # Check if the parent is assigned a destination that has no assembly template spot for the item, remove from queryset
            if parent.assembly_part:
                parent_tree = parent.assembly_part.get_children()
                if parent_tree:
                    for ap in parent_tree:
                        if ap not in item.part.assembly_parts.all():
                            x = False
                        else:
                            x = True
                            break
                    if not x:
                        parent_items = parent_items.exclude(id=parent.id)

        context.update({"parent_items": parent_items})
        context.update({"inventory_item": item})
        return context


class InventoryAjaxParentActionView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        subassembly = Inventory.objects.get(id=self.kwargs["pk"])
        parent = Inventory.objects.get(id=self.kwargs["parent_pk"])

        if parent.assembly_part:
            assembly_parts = parent.assembly_part.get_children()
            assembly_part = assembly_parts.get(part=subassembly.part)
        else:
            assembly_part = None

        subassembly.location = parent.location
        subassembly.build = parent.build
        subassembly.parent = parent
        subassembly.assembly_part = assembly_part
        subassembly.assigned_destination_root = parent.assigned_destination_root
        subassembly.save()

        # Call the function to create an Action history chain for this event
        _create_action_history(subassembly, Action.SUBCHANGE, self.request.user)
        _create_action_history(parent, Action.SUBCHANGE, self.request.user, subassembly)

        # Get any subassembly children items, move their location to match parent and add Action to history
        subassemblies = subassembly.get_descendants()
        assembly_parts_added = []
        for item in subassemblies:
            if assembly_part:
                sub_assembly_parts = subassembly.assembly_part.get_descendants()
                sub_assembly_part = sub_assembly_parts.filter(part=item.part)
                for sub in sub_assembly_part:
                    if sub.id not in assembly_parts_added:
                        item.assembly_part = sub
                        assembly_parts_added.append(sub.id)
                        break

            item.location = subassembly.location
            item.build = subassembly.build
            item.assigned_destination_root = subassembly.assigned_destination_root
            item.detail = "Parent added to new sub-assembly"
            item.save()
            # Add Action Record if Location change
            # Call the function to create an Action history chain for this event
            _create_action_history(
                item, Action.LOCATIONCHANGE, self.request.user, subassembly
            )

        return reverse("inventory:ajax_inventory_detail", args=(self.kwargs["pk"],))


class InventoryAjaxSubassemblyListView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/ajax_inventory_add_subassembly.html"

    def get_context_data(self, **kwargs):
        context = super(InventoryAjaxSubassemblyListView, self).get_context_data(
            **kwargs
        )
        parent = Inventory.objects.get(id=self.kwargs["parent_pk"])
        if parent.assembly_part:
            assembly_parts = assembly_part.get_children()
            part_templates = Part.objects.filter(assembly_parts__in=assembly_parts)
            inventory_items = (
                Inventory.objects.filter(part__in=part_templates)
                .filter(build__isnull=True)
                .exclude(location__root_type="Trash")
            )
        else:
            assembly_parts = AssemblyPart.objects.filter(part=parent.part)
            assembly_parts_list = []
            for ap in assembly_parts:
                result_list = AssemblyPart.objects.get(id=ap.id).get_children()
                assembly_parts_list = list(chain(assembly_parts_list, result_list))
            part_templates = Part.objects.filter(assembly_parts__in=assembly_parts_list)
            inventory_items = (
                Inventory.objects.filter(part__in=part_templates)
                .filter(assembly_part__isnull=True)
                .filter(parent__isnull=True)
                .exclude(location__root_type="Trash")
            )

        context.update({"inventory_items": inventory_items})
        context.update({"parent": parent})
        return context


class InventoryAjaxSubassemblyActionView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        subassembly = Inventory.objects.get(id=self.kwargs["pk"])
        parent = Inventory.objects.get(id=self.kwargs["parent_pk"])
        if parent.assembly_part:
            assembly_parts = parent.assembly_part.get_children()
            assembly_part = assembly_parts.get(part=subassembly.part)
        else:
            assembly_part = None

        subassembly.location = parent.location
        subassembly.build = parent.build
        subassembly.parent = parent
        subassembly.assembly_part = assembly_part
        subassembly.save()

        # Call the function to create an Action history chain for this event
        _create_action_history(subassembly, Action.SUBCHANGE, self.request.user)
        _create_action_history(parent, Action.SUBCHANGE, self.request.user, subassembly)

        # Get any subassembly children items, move their location to match parent and add Action to history
        subassemblies = Inventory.objects.get(id=subassembly.id).get_descendants()
        assembly_parts_added = []
        for item in subassemblies:
            if assembly_part:
                sub_assembly_parts = subassembly.assembly_part.get_descendants()
                sub_assembly_part = sub_assembly_parts.filter(part=item.part)
                for sub in sub_assembly_part:
                    if sub.id not in assembly_parts_added:
                        item.assembly_part = sub
                        assembly_parts_added.append(sub.id)
                        break

            item.location = subassembly.location
            item.build = subassembly.build
            item.detail = "Parent added to new sub-assembly"
            item.save()
            # Add Action Record if Location change
            # Call the function to create an Action history chain for this event
            _create_action_history(
                item, Action.LOCATIONCHANGE, self.request.user, subassembly
            )

        return reverse(
            "inventory:ajax_inventory_detail", args=(self.kwargs["parent_pk"],)
        )


class InventoryAjaxLocationDetailView(LoginRequiredMixin, DetailView):
    model = Location
    template_name = "inventory/ajax_inventory_location_detail.html"
    context_object_name = "location"


class InventoryAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Inventory
    context_object_name = "inventory_item"
    template_name = "inventory/ajax_inventory_confirm_delete.html"
    success_url = reverse_lazy("inventory:inventory_home")
    permission_required = "inventory.delete_inventory"
    redirect_field_name = "home"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            "message": "Successfully submitted form data.",
            "parent_id": self.object.parent_id,
        }
        self.object.delete()
        return JsonResponse(data)


# Base Views

# View to get direct link to an Inventory item
class InventoryDetailView(LoginRequiredMixin, DetailView):
    model = Inventory
    template_name = "inventory/inventory_detail.html"
    context_object_name = "inventory_item"
    queryset = (
        Inventory.objects.prefetch_related("actions__user")
        .prefetch_related("actions__location")
        .prefetch_related("actions__photos")
        .prefetch_related("photos")
        .prefetch_related("inventory_deployments")
        .select_related(
            "location", "parent", "revision__part", "build", "part", "assembly_part"
        )
    )

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

        # Get Inventory items by Root Locations
        inventory_location_data = []
        root_locations = Location.objects.root_nodes().exclude(root_type="Trash")
        for root in root_locations:
            locations_list = root.get_descendants(include_self=True).values_list(
                "id", flat=True
            )
            items = self.object.part.inventory.filter(location__in=locations_list)
            if items:
                data = {
                    "location_root": root,
                    "inventory_items": items,
                }
                inventory_location_data.append(data)

        context.update(
            {
                "part_types": part_types,
                "printers": printers,
                "custom_fields": custom_fields,
                "node_type": node_type,
                "inventory_location_data": inventory_location_data,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# View to get main Inventory landing page
class InventoryHomeView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/inventory_home.html"
    context_object_name = "inventory_item"

    def get_context_data(self, **kwargs):
        context = super(InventoryHomeView, self).get_context_data(**kwargs)
        # Add Parts list to context to build navtree filter
        part_types = PartType.objects.all()
        context.update(
            {
                "part_types": part_types,
                "node_type": node_type,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


"""
Deployment views
"""


class InventoryDeploymentAjaxUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = InventoryDeployment
    form_class = InventoryDeploymentForm
    context_object_name = "inventory_deployment"
    template_name = "inventory/ajax_inventory_deployment_form.html"

    def get_context_data(self, **kwargs):
        context = super(InventoryDeploymentAjaxUpdateView, self).get_context_data(
            **kwargs
        )

        if "action_type" in self.kwargs:
            context["action_type"] = self.kwargs["action_type"]
        else:
            context["action_type"] = None

        return context

    def form_valid(self, form):
        self.object = form.save()
        action_type = "deploymentdetails"
        self.object.inventory.detail = "%s Details changed." % (
            self.object.deployment.deployment_number
        )
        self.object.inventory.save()
        # Create Build Action record for deployment
        action_record = _create_action_history(
            self.object.inventory,
            action_type,
            self.request.user,
        )

        # Update Deployment Action items to match any date changes
        actions = self.object.get_actions()
        for action in actions:
            print(action.action_type)
            if action.action_type == Action.STARTDEPLOYMENT:
                action.created_at = self.object.deployment_start_date

            if action.action_type == Action.DEPLOYMENTBURNIN:
                action.created_at = self.object.deployment_burnin_date

            if action.action_type == Action.DEPLOYMENTTOFIELD:
                action.created_at = self.object.deployment_to_field_date

            if action.action_type == Action.DEPLOYMENTRECOVER:
                action.created_at = self.object.deployment_recovery_date

            if action.action_type == Action.DEPLOYMENTRETIRE:
                action.created_at = self.object.deployment_retire_date

            action.save()

        if self.request.is_ajax():
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.inventory.id,
                "object_type": self.object.inventory.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse(
            "inventory:ajax_inventory_detail", args=(self.object.inventory.id,)
        )


class DeploymentAjaxSnapshotCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = DeploymentSnapshot
    form_class = DeploymentSnapshotForm
    template_name = "inventory/ajax_snapshot_form.html"
    context_object_name = "deployment"

    def get_context_data(self, **kwargs):
        context = super(DeploymentAjaxSnapshotCreateView, self).get_context_data(
            **kwargs
        )
        context.update({"deployment": Deployment.objects.get(id=self.kwargs["pk"])})
        return context

    def get_form_kwargs(self):
        kwargs = super(DeploymentAjaxSnapshotCreateView, self).get_form_kwargs()
        if "pk" in self.kwargs:
            kwargs["pk"] = self.kwargs["pk"]
        return kwargs

    def get_success_url(self):
        return reverse("deployments:ajax_deployment_detail", args=(self.kwargs["pk"],))

    def form_valid(self, form, **kwargs):
        deployment = Deployment.objects.get(pk=self.kwargs["pk"])
        base_location = Location.objects.get(root_type="Snapshots")
        # snapshot_location = Location.objects.get(root_type='Snapshots')
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
                "message": "Successfully submitted form data.",
                "object_id": deployment.id,
            }
            return JsonResponse(data)
        else:
            return response


class DeploymentSnapshotAjaxDetailView(LoginRequiredMixin, DetailView):
    model = DeploymentSnapshot
    context_object_name = "deployment_snapshot"
    template_name = "inventory/ajax_deployment_snapshot_detail.html"


class DeploymentSnapshotAjaxDeleteView(DeleteView):
    model = DeploymentSnapshot
    template_name = "inventory/ajax_deployment_confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            "message": "Successfully submitted form data.",
            "parent_id": self.object.location_id,
        }
        self.object.delete()
        return JsonResponse(data)
