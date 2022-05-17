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

import json
import os

from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from common.util.mixins import AjaxFormMixin
from .models import Build, BuildAction, BuildSnapshot, InventorySnapshot, PhotoNote
from .forms import *
from roundabout.assemblies.models import Assembly, AssemblyPart, AssemblyRevision
from roundabout.locations.models import Location
from roundabout.inventory.models import Inventory, Action
from roundabout.inventory.utils import _create_action_history, logged_user_review_items
from roundabout.admintools.models import Printer
# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels
labels = set_app_labels()
# Import environment variables from .env files
import environ
env = environ.Env()
# Global variables for views.py functions
node_type = 'builds'

# Load the javascript navtree
def load_builds_navtree(request):
    node_id = request.GET.get('id')

    reviewer_list = logged_user_review_items(request.user, 'inv')

    if node_id == '#' or not node_id:
        locations = Location.objects.prefetch_related('builds__assembly__assembly_parts__part__part_type') \
                    .prefetch_related('builds__inventory__part__part_type').prefetch_related('builds__deployments')
        return render(request, 'builds/ajax_build_navtree.html', {'locations': locations, 'reviewer_list': reviewer_list})
    else:
        build_pk = node_id.split('_')[1]
        build = Build.objects.prefetch_related('assembly_revision__assembly_parts').prefetch_related('inventory').get(id=build_pk)
        return render(request, 'builds/build_tree_assembly.html', {'assembly_parts': build.assembly_revision.assembly_parts,
                                                                   'inventory_qs': build.inventory,
                                                                   'location_pk': build.location_id,
                                                                   'build_pk': build_pk, 
                                                                   'reviewer_list': reviewer_list})


# Internal function to copy Inventory items for Build Snapshots
def _make_tree_copy(root_part, new_location, build_snapshot, parent=None ):
    # Makes a copy of the tree starting at "root_part", move to new Location, reparenting it to "parent"
    if root_part.part.friendly_name:
        part_name = root_part.part.friendly_name
    else:
        part_name = root_part.part.name

    new_item = InventorySnapshot.objects.create(location=new_location, inventory=root_part, parent=parent, build=build_snapshot, order=part_name)

    for child in root_part.get_children():
        _make_tree_copy(child, new_location, build_snapshot, new_item)


# Function to create Serial Number from Assembly Number selection, load result into form to preview
def load_new_build_id_number(request):
    # Set pattern variables from .env configuration
    RDB_SERIALNUMBER_CREATE = env.bool('RDB_SERIALNUMBER_CREATE', default=False)
    RDB_SERIALNUMBER_OOI_DEFAULT_PATTERN = env.bool('RDB_SERIALNUMBER_OOI_DEFAULT_PATTERN', default=False)

    # Set variables from JS request
    assembly_id = request.GET.get('assembly_id')
    new_build_id_number = ''
    new_serial_number = ''

    if RDB_SERIALNUMBER_CREATE:
        if assembly_id:
            try:
                assembly_obj = Assembly.objects.get(id=assembly_id)
            except Assembly.DoesNotExist:
                assembly_obj = None

            if assembly_obj:
                if RDB_SERIALNUMBER_OOI_DEFAULT_PATTERN:
                    regex = '^(.*?)-[a-zA-Z0-9_]{5}$'
                    fragment_length = 5
                    fragment_default = '20001'
                    use_assembly_number = True
                else:
                    # Basic default serial number pattern (1,2,3,... etc.)
                    regex = '^(.*?)'
                    fragment_length = False
                    fragment_default = '1'
                    use_assembly_number = False

                builds_qs = Build.objects.filter(assembly=assembly_obj).filter(build_number__iregex=regex)
                if builds_qs:
                    build_last = builds_qs.latest('id')
                    try:
                        last_serial_number_fragment = int(build_last.build_number.split('-')[-1])
                        new_serial_number_fragment = last_serial_number_fragment + 1
                    except:
                        new_serial_number_fragment = fragment_default
                    # Fill fragment with leading zeroes if necessary
                    if fragment_length:
                        new_serial_number_fragment = str(new_serial_number_fragment).zfill(fragment_length)
                else:
                    new_serial_number_fragment = fragment_default

                if use_assembly_number:
                    new_serial_number = assembly_obj.assembly_number + '-' + str(new_serial_number_fragment)
                else:
                    new_serial_number = str(new_serial_number_fragment)

    data = {
        'new_serial_number': new_serial_number,
    }
    return JsonResponse(data)


# Function to load Assembly Revisions based on Assembly
def load_assembly_revisions(request):
    assembly_id = request.GET.get('assembly_id')
    revisions = AssemblyRevision.objects.none()
    if assembly_id:
        revisions = AssemblyRevision.objects.filter(assembly_id=assembly_id)
    return render(request, 'builds/revisions_dropdown_list_options.html', {'revisions': revisions,})


## CBV views for Builds app ##
# ----------------------------
# Landing page for Builds
class BuildHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'builds/build_list.html'
    context_object_name = 'builds'

    def get_context_data(self, **kwargs):
        context = super(BuildHomeView, self).get_context_data(**kwargs)
        context.update({
            'node_type': node_type,
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# Direct Detail view for Builds
class BuildDetailView(LoginRequiredMixin, DetailView):
    model = Build
    context_object_name = 'build'
    template_name='builds/build_detail.html'

    def get_context_data(self, **kwargs):
        context = super(BuildDetailView, self).get_context_data(**kwargs)
        # Get Printers to display in print dropdown
        printers = Printer.objects.all()
        # Get assembly part data and inventory data to calculate completeness
        total_parts = AssemblyPart.objects.filter(assembly_revision=self.object.assembly_revision).count()
        total_inventory = self.object.inventory.count()

        if total_parts > 0:
            percent_complete = round( (total_inventory / total_parts) * 100 )
        else:
            percent_complete = None

        action_record = None
        bar_class = None
        bar_width = None

        # Get Lat/Long, Depth if Deployed
        if self.object.is_deployed:
            current_deployment = self.object.current_deployment()
            action_record = DeploymentAction.objects.filter(deployment=current_deployment).filter(action_type='deploymenttosea').first()

        context.update({
            'printers': printers,
            'node_type': node_type,
            'current_deployment': self.object.current_deployment(),
            'percent_complete': percent_complete,
            'action_record': action_record,
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# AJAX Detail view for builds
class BuildAjaxDetailView(LoginRequiredMixin, DetailView):
    model = Build
    context_object_name = 'build'
    template_name='builds/ajax_build_detail.html'

    def get_context_data(self, **kwargs):
        context = super(BuildAjaxDetailView, self).get_context_data(**kwargs)
        # Get Printers to display in print dropdown
        printers = Printer.objects.all()
        # Get assembly part data and inventory data to calculate completeness
        total_parts = AssemblyPart.objects.filter(assembly_revision=self.object.assembly_revision).count()
        total_inventory = self.object.inventory.count()

        if total_parts > 0:
            percent_complete = round( (total_inventory / total_parts) * 100 )
        else:
            percent_complete = None

        action_record = None
        bar_class = None
        bar_width = None

        user_rev_deployment_events = False

        latest_deployment = self.object.get_latest_deployment()
        if self.request.user.reviewer_deployments.exists():
            if latest_deployment in self.request.user.reviewer_deployments.all():
                user_rev_deployment_events = True

        # Get Lat/Long, Depth if Deployed
        if self.object.is_deployed:
            current_deployment = self.object.current_deployment()
            action_record = DeploymentAction.objects.filter(deployment=current_deployment).filter(action_type='deploymenttosea').first()

        context.update({
            'printers': printers,
            'node_type': node_type,
            'current_deployment': self.object.current_deployment(),
            'percent_complete': percent_complete,
            'action_record': action_record,
            'user_rev_deployment_events': user_rev_deployment_events
        })
        return context


# Create view for assemblies
class BuildAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Build
    form_class = BuildForm
    context_object_name = 'build'
    template_name='builds/ajax_build_form.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = BuildHyperlinkFormset(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form, link_formset=link_formset))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = BuildHyperlinkFormset(self.request.POST, instance=self.object)

        if form.is_valid() and link_formset.is_valid():
            return self.form_valid(form,link_formset)
        return self.form_invalid(form,link_formset)


    def form_valid(self, form, formset):
        self.object = form.save()

        # Adding Build to hyperlink objects
        for link_form in formset:
            link = link_form.save(commit=False)
            if link.text and link.url:
                link.parent = self.object
                link.save()

        # Call the function to create an Action history chain
        _create_action_history(self.object, Action.ADD, self.request.user)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def form_invalid(self, form, formset):
        if self.request.is_ajax():
            if not form.is_valid():
                # show form errors before formset errors
                return JsonResponse(form.errors, status=400)
            else:
                # only show formset errors if there are no form errors
                # because it is unclear how to combine form and formset errors in a way that doesnt break project.js:handleFormError()
                return JsonResponse(formset.errors, status=400, safe=False)
        else:
            return self.render_to_response(self.get_context_data(form=form, link_formset=formset))

    def get_success_url(self):
        return reverse('builds:ajax_builds_detail', args=(self.object.id,))


# Update view for builds
class BuildAjaxUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = Build
    form_class = BuildForm
    context_object_name = 'build'
    template_name='builds/ajax_build_form.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = BuildHyperlinkFormset(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form, link_formset=link_formset))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        link_formset = BuildHyperlinkFormset(self.request.POST, instance=self.object)

        if form.is_valid() and link_formset.is_valid():
            return self.form_valid(form,link_formset)
        return self.form_invalid(form,link_formset)


    def form_valid(self, form, formset):
        self.object = form.save()

        # Adding Build to hyperlink objects
        for link_form in formset:
            link = link_form.save(commit=False)
            if link.text and link.url:
                if link_form['DELETE'].data:
                    link.delete()
                else:
                    link.parent = self.object
                    link.save()

        # Create new Action record
        # Call the function to create an Action history chain
        _create_action_history(self.object, Action.UPDATE, self.request.user)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def form_invalid(self, form, formset):
        if self.request.is_ajax():
            if not form.is_valid():
                # show form errors before formset errors
                return JsonResponse(form.errors, status=400)
            else:
                # only show formset errors if there are no form errors
                # because it is unclear how to combine form and formset errors in a way that doesnt break project.js:handleFormError()
                return JsonResponse(formset.errors, status=400, safe=False)
        else:
            return self.render_to_response(self.get_context_data(form=form, link_formset=formset))

    def get_success_url(self):
        return reverse('builds:ajax_builds_detail', args=(self.object.id,))


# Action view to handle discrete form actions
class BuildAjaxActionView(BuildAjaxUpdateView):

    def get_form_class(self):
        ACTION_FORMS = {
            'locationchange' : BuildActionLocationChangeForm,
            'test': BuildActionTestForm,
            'flag': BuildActionFlagForm,
            "retirebuild" : BuildActionRetireForm,

        }
        action_type = self.kwargs['action_type']
        form_class_name = ACTION_FORMS[action_type]

        return form_class_name

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        self.form_invalid(form)

    def form_valid(self, form):
        action_type = self.kwargs['action_type']
        action_form = form.save()
        # Create new Action record
        # Call the function to create an Action history chain for this event
        _create_action_history(self.object, action_type, self.request.user)

        if self.kwargs['action_type'] == Action.LOCATIONCHANGE:
            # Get any subassembly children items, move their locations to match parent and add Action to history
            subassemblies = self.object.inventory.all()
            assembly_parts_added = []
            for item in subassemblies:
                item.location = self.object.location
                item.save()
                # Call the function to create an Action history chain for this event
                _create_action_history(item, action_type, self.request.user, self.object)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'location_id': self.object.location.id,
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response


class BuildNoteAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Action
    form_class = BuildActionPhotoNoteForm
    context_object_name = 'action'
    template_name='builds/ajax_inventory_photo_note_form.html'

    def get_context_data(self, **kwargs):
        context = super(BuildNoteAjaxCreateView, self).get_context_data(**kwargs)
        build = Build.objects.get(id=self.kwargs['pk'])
        context.update({
            'build': build
        })
        return context

    def get_initial(self):
        build = Build.objects.get(id=self.kwargs['pk'])
        return { 'build': build.id, 'location': build.location_id }

    def form_valid(self, form):
        self.object = form.save()
        self.object.user = self.request.user
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
                'object_id': self.object.build_id,
                'object_type': self.object.build.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse('builds:ajax_builds_detail', args=(self.object.build_id, ))


class BuildPhotoUploadAjaxCreateView(View):
    def get(self, request, **kwargs):
        build = Build.objects.get(id=self.kwargs['pk'])
        form = BuildActionPhotoUploadForm()
        return render(self.request, 'builds/ajax_inventory_photo_note_form.html', {'build': build,})

    def post(self, request, **kwargs):
        form = BuildActionPhotoUploadForm(self.request.POST, self.request.FILES)

        if form.is_valid():
            photo_note = form.save()
            photo_note.build_id = self.kwargs['pk']
            photo_note.user = self.request.user
            photo_note.save()
            data = {'is_valid': True,
                    'name': photo_note.photo.name,
                    'url': photo_note.photo.url,
                    'photo_id': photo_note.id,
                    'file_type': photo_note.file_type() }
        else:
            data = {'is_valid': False,
                    'errors': form.errors,}
        return JsonResponse(data)


class BuildAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Build
    template_name = 'builds/ajax_build_confirm_delete.html'
    permission_required = 'builds.delete_build'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.location.id,
            'parent_type': 'locations',
            'object_type': self.object.get_object_type(),
        }
        self.object.delete()

        return JsonResponse(data)


# Create a new Snapshot copy of a Build
class BuildAjaxSnapshotCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = BuildSnapshot
    form_class = BuildSnapshotForm
    template_name = 'builds/ajax_snapshot_form.html'
    context_object_name = 'build'

    def get_context_data(self, **kwargs):
        context = super(BuildAjaxSnapshotCreateView, self).get_context_data(**kwargs)
        context.update({
            'build': Build.objects.get(id=self.kwargs['pk'])
        })
        return context

    def get_form_kwargs(self):
        kwargs = super(BuildAjaxSnapshotCreateView, self).get_form_kwargs()
        if 'pk' in self.kwargs:
            kwargs['pk'] = self.kwargs['pk']
        return kwargs

    def get_success_url(self):
        return reverse('builds:ajax_builds_detail', args=(self.kwargs['pk'], ))

    def form_valid(self, form, **kwargs):
        build = Build.objects.get(pk=self.kwargs['pk'])
        #base_location = Location.objects.get(root_type='Snapshots')
        #snapshot_location = Location.objects.get(root_type='Snapshots')
        inventory_items = build.inventory.all()

        build_snapshot = form.save()
        build_snapshot.build = build
        build_snapshot.deployment = build.current_deployment()
        if build.current_deployment():
            build_snapshot.deployment_status = build.current_deployment().current_status
        build_snapshot.location = build.location
        build_snapshot.time_at_sea = build.time_at_sea
        build_snapshot.save()

        for item in inventory_items:
            if item.is_root_node():
                _make_tree_copy(item, build.location, build_snapshot, item.parent)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': build.id,
                'object_type': build.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response
