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
from pprint import pprint
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction

from .models import Assembly, AssemblyPart, AssemblyType, AssemblyDocument, AssemblyRevision
from .forms import AssemblyForm, AssemblyPartForm, AssemblyTypeForm, AssemblyRevisionForm, AssemblyRevisionFormset, AssemblyDocumentationFormset, AssemblyTypeDeleteForm
from roundabout.parts.models import PartType, Part
from roundabout.inventory.models import Action
from common.util.mixins import AjaxFormMixin


# General functions for use in Assembly views
# ------------------------------------------------------------------------------

# Makes a copy of the tree starting at "root_part", move to new Assembly, reparenting it to "parent"
def _make_tree_copy(root_part, new_assembly, parent=None):
    new_ap = AssemblyPart.objects.create(assembly=new_assembly, part=root_part.part, parent=parent, order=root_part.order)

    for child in root_part.get_children():
        _make_tree_copy(child, new_assembly, new_ap)


# Makes a copy of the Assembly Revisiontree starting at "root_part",
# move to new Revision, reparenting it to "parent"
def _make_revision_tree_copy(root_part, new_revision, parent=None):
    new_ap = AssemblyPart.objects.create(assembly_revision=new_revision, part=root_part.part, parent=parent, order=root_part.order)

    for child in root_part.get_children():
        _make_revision_tree_copy(child, new_revision, new_ap)


# Load the javascript navtree
def load_assemblies_navtree(request):
    node_id = request.GET.get('id')

    if node_id == '#' or not node_id:
        assembly_types = AssemblyType.objects.prefetch_related('assemblies__assembly_revisions')
        return render(request, 'assemblies/ajax_assembly_navtree.html', {'assembly_types': assembly_types})
    else:
        revision_pk = node_id.split('_')[1]
        revision_obj = AssemblyRevision.objects.prefetch_related('assembly_parts').get(id=revision_pk)
        return render(request, 'assemblies/assembly_tree_parts.html', {'assembly_parts': revision_obj.assembly_parts})


# Function to load Parts based on Part Type filter
def load_part_templates(request):
    part_type = request.GET.get('part_type')
    if part_type == 'All':
        part_list = Part.objects.all()
    else:
        part_list = Part.objects.filter(part_type=part_type)
    return render(request, 'inventory/part_templates_dropdown_list_options.html', {'parts': part_list})


# Function to load available Assembly Parts based on Assembly
def load_assembly_parts(request):
    assembly_id = request.GET.get('assembly')
    assembly_parts_list = AssemblyPart.objects.none()
    if assembly_id:
        assembly = Assembly.objects.get(id=assembly_id)
        assembly_parts_list = AssemblyPart.objects.filter(assembly=assembly).prefetch_related('part')
    return render(request, 'inventory/assemblyparts_dropdown_list_options.html', {'assembly_parts': assembly_parts_list})


## CBV views for Assembly app ##
# ------------------------------------------------------------------------------
# Landing page for assemblies
class AssemblyHomeView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'assemblies/assembly_list.html'
    context_object_name = 'assemblies'
    permission_required = 'assemblies.view_assembly'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(AssemblyHomeView, self).get_context_data(**kwargs)
        context.update({
            'node_type': 'assemblies',
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# Direct Detail view for Assembly Part
class AssemblyDetailView(LoginRequiredMixin, DetailView):
    model = Assembly
    context_object_name = 'assembly'
    template_name='assemblies/assembly_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AssemblyDetailView, self).get_context_data(**kwargs)
        context.update({
            'node_type': 'assemblies'
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# AJAX Detail view for assemblies
class AssemblyAjaxDetailView(LoginRequiredMixin, DetailView):
    model = Assembly
    context_object_name = 'assembly'
    template_name='assemblies/ajax_assembly_detail.html'


# Create view for assemblies
class AssemblyAjaxCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = Assembly
    form_class = AssemblyForm
    context_object_name = 'assembly'
    template_name='assemblies/ajax_assembly_form.html'
    permission_required = 'assemblies.add_assembly'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = AssemblyDocumentationFormset(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = AssemblyDocumentationFormset(
            self.request.POST, instance=self.object)

        if (form.is_valid() and documentation_form.is_valid()):
            return self.form_valid(form, documentation_form)
        return self.form_invalid(form, documentation_form)

    def form_valid(self, form, documentation_form):
        self.object = form.save()
        # Create an initial Revision for this Assembly
        revision_code = form.cleaned_data['revision_code']
        revision = AssemblyRevision.objects.create(revision_code=revision_code, assembly=self.object)

        # Save the Documentation inline model form
        documentation_form.instance = revision
        documentation_instances = documentation_form.save(commit=False)
        # Update Documentation objects to have Revision key
        for instance in documentation_instances:
            print(instance)
        documentation_form.save()

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

    def form_invalid(self, form, documentation_form):
        form_errors = documentation_form.errors

        if self.request.is_ajax():
            data = form.errors
            return JsonResponse(data, status=400)
        else:
            return self.render_to_response(self.get_context_data(form=form, revision_form=revision_form, documentation_form=documentation_form, form_errors=form_errors))

    def get_success_url(self):
        return reverse('assemblies:ajax_assemblies_detail', args=(self.object.id,))


# View to copy full Assembly Template to new Assembly object
class AssemblyAjaxCopyView(AssemblyAjaxCreateView):

    def get_context_data(self, **kwargs):
        context = super(AssemblyAjaxCopyView, self).get_context_data(**kwargs)
        context.update({
            'assembly_to_copy': Assembly.objects.get(id=self.kwargs['assembly_to_copy_pk'])
        })
        return context

    def get_form_kwargs(self):
        kwargs = super(AssemblyAjaxCopyView, self).get_form_kwargs()
        if 'assembly_to_copy_pk' in self.kwargs:
            kwargs['assembly_to_copy_pk'] = self.kwargs['assembly_to_copy_pk']
        return kwargs

    def form_valid(self, form, documentation_form, **kwargs):
        self.object = form.save()
        # Create an initial Revision for this Assembly
        revision_code = form.cleaned_data['revision_code']
        revision = AssemblyRevision.objects.create(revision_code=revision_code, assembly=self.object)

        # Save the Documentation inline model form
        documentation_form.instance = revision
        documentation_instances = documentation_form.save(commit=False)
        # Update Documentation objects to have Revision key
        for instance in documentation_instances:
            print(instance)
        documentation_form.save()

        # Need to copy the current Revision template to new Revision
        assembly_to_copy = Assembly.objects.get(pk=self.kwargs['assembly_to_copy_pk'])
        assembly_revision_to_copy = assembly_to_copy.assembly_revisions.latest()
        assembly_parts = assembly_revision_to_copy.assembly_parts.all()

        for ap in assembly_parts:
            if ap.is_root_node():
                _make_revision_tree_copy(ap, revision, ap.parent)

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


# Update view for assemblies
class AssemblyAjaxUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = Assembly
    form_class = AssemblyForm
    context_object_name = 'assembly'
    template_name='assemblies/ajax_assembly_form.html'
    permission_required = 'assemblies.change_assembly'
    redirect_field_name = 'home'

    def form_valid(self, form):
        self.object = form.save()

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

    def get_success_url(self):
        return reverse('assemblies:ajax_assemblies_detail', args=(self.object.id,))


class AssemblyAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Assembly
    template_name = 'assemblies/ajax_assembly_confirm_delete.html'
    context_object_name = 'assembly'
    permission_required = 'assemblies.delete_assembly'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.id,
            'object_type': self.object.get_object_type(),
        }
        self.object.delete()

        return JsonResponse(data)


### CBV views for AssemblyRevision model ###

# Direct Detail view for Assembly Revision
class AssemblyRevisionDetailView(LoginRequiredMixin, DetailView):
    model = AssemblyRevision
    context_object_name = 'assembly_revision'
    template_name='assemblies/assembly_revision_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AssemblyRevisionDetailView, self).get_context_data(**kwargs)
        context.update({
            'node_type': 'assemblyrevisions'
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# AJAX Detail view for Assembly Revision
class AssemblyRevisionAjaxDetailView(LoginRequiredMixin, DetailView):
    model = AssemblyRevision
    context_object_name = 'assembly_revision'
    template_name='assemblies/ajax_assembly_revision_detail.html'


# Create new Assembly Revision form
class AssemblyRevisionAjaxCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = AssemblyRevision
    form_class = AssemblyRevisionForm
    context_object_name = 'assembly_revision'
    template_name='assemblies/ajax_assembly_revision_form.html'
    permission_required = 'assemblies.add_assembly'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(AssemblyRevisionAjaxCreateView, self).get_context_data(**kwargs)
        assembly_revision_pk = self.kwargs['assembly_revision_pk']
        copy_revision = AssemblyRevision.objects.get(id=assembly_revision_pk)

        context.update({
            'copy_revision': copy_revision,
        })
        return context

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = AssemblyDocumentationFormset(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = AssemblyDocumentationFormset(
            self.request.POST, instance=self.object)

        if (form.is_valid() and documentation_form.is_valid()):
            return self.form_valid(form, documentation_form)
        return self.form_invalid(form, documentation_form)

    def get_initial(self):
        #Returns the initial data from current revision
        initial = super(AssemblyRevisionAjaxCreateView, self).get_initial()
        # get the current revision object, prepopolate fields
        assembly_revision_pk = self.kwargs['assembly_revision_pk']
        assembly_revision = AssemblyRevision.objects.get(id=assembly_revision_pk)
        initial['assembly'] = assembly_revision.assembly
        initial['revision_code'] = None

        return initial

    def get_form_kwargs(self):
        kwargs = super(AssemblyRevisionAjaxCreateView, self).get_form_kwargs()
        if 'assembly_revision_pk' in self.kwargs:
            kwargs['assembly_revision_pk'] = self.kwargs['assembly_revision_pk']
        return kwargs

    def form_valid(self, form, documentation_form):
        self.object = form.save()
        documentation_form.instance = self.object
        documentation_form.save()

        # Need to copy the current Revision template to new Revision
        assembly_revision_pk = self.kwargs['assembly_revision_pk']
        assembly_revision = AssemblyRevision.objects.get(id=assembly_revision_pk)
        assembly_parts = assembly_revision.assembly_parts.all()

        for ap in assembly_parts:
            if ap.is_root_node():
                _make_revision_tree_copy(ap, self.object, ap.parent)

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

    def form_invalid(self, form, documentation_form):
        form_errors = documentation_form.errors

        if self.request.is_ajax():
            data = form.errors
            return JsonResponse(data, status=400)
        else:
            return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form, form_errors=form_errors))

    def get_success_url(self):
        return reverse('assemblies:ajax_assemblyrevision_detail', args=(self.object.id,))


class AssemblyRevisionAjaxUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = AssemblyRevision
    form_class = AssemblyRevisionForm
    context_object_name = 'assembly_revision'
    template_name='assemblies/ajax_assembly_revision_form.html'
    permission_required = 'assemblies.add_assembly'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = AssemblyDocumentationFormset(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = AssemblyDocumentationFormset(
            self.request.POST, instance=self.object)

        if (form.is_valid() and documentation_form.is_valid()):
            return self.form_valid(form, documentation_form)
        return self.form_invalid(form, documentation_form)

    def form_valid(self, form, documentation_form):
        self.object = form.save()
        documentation_form.instance = self.object
        documentation_form.save()
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

    def form_invalid(self, form, documentation_form):
        form_errors = documentation_form.errors

        if self.request.is_ajax():
            data = form.errors
            return JsonResponse(data, status=400)
        else:
            return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form, form_errors=form_errors))

    def get_success_url(self):
        return reverse('assemblies:ajax_assemblyrevision_detail', args=(self.object.id,))


class AssemblyRevisionAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = AssemblyRevision
    template_name = 'assemblies/ajax_assembly_revision_confirm_delete.html'
    context_object_name = 'assembly_revision'
    permission_required = 'assemblies.delete_assembly'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.id,
            'object_type': self.object.get_object_type(),
        }
        self.object.delete()

        return JsonResponse(data)


### CBV views for AssemblyPart model ###

# Direct Detail view for Assembly Part
class AssemblyPartDetailView(LoginRequiredMixin, DetailView):
    model = AssemblyPart
    context_object_name = 'assembly_part'
    template_name='assemblies/assemblypart_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AssemblyPartDetailView, self).get_context_data(**kwargs)
        context.update({
            'node_type': self.object.get_object_type()
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# AJAX Detail view for Assembly Part
class AssemblyPartAjaxDetailView(LoginRequiredMixin, DetailView):
    model = AssemblyPart
    context_object_name = 'assembly_part'
    template_name='assemblies/ajax_assemblypart_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AssemblyPartAjaxDetailView, self).get_context_data(**kwargs)
        part_has_configs = False
        if self.object.part.config_name_events.exists():
            if self.object.part.config_name_events.first().config_names.filter(config_type='conf').exists():
                part_has_configs = True
        context.update({
            'node_type': self.object.get_object_type(),
            'part_has_configs': part_has_configs
        })
        return context


# Create view for Assembly Part
class AssemblyPartAjaxCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = AssemblyPart
    form_class = AssemblyPartForm
    template_name='assemblies/ajax_assemblypart_form.html'
    context_object_name = 'assembly_part'
    permission_required = 'assemblies.add_assembly'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(AssemblyPartAjaxCreateView, self).get_context_data(**kwargs)
        assembly_revision = AssemblyRevision.objects.get(id=self.kwargs['assembly_revision_pk'])

        context.update({
            'part_types': PartType.objects.all(),
            'assembly_revision': assembly_revision,
            'builds': assembly_revision.builds.all()
        })
        if 'parent_pk' in self.kwargs:
            context.update({
                'parent': AssemblyPart.objects.get(id=self.kwargs['parent_pk'])
            })
        return context

    def get_form_kwargs(self):
        kwargs = super(AssemblyPartAjaxCreateView, self).get_form_kwargs()
        kwargs['assembly_revision_pk'] = self.kwargs['assembly_revision_pk']
        if 'parent_pk' in self.kwargs:
            kwargs['parent_pk'] = self.kwargs['parent_pk']
        return kwargs

    def get_initial(self):
        #Returns the initial data to use for forms on this view.
        initial = super(AssemblyPartAjaxCreateView, self).get_initial()
        initial['assembly_revision'] = self.kwargs['assembly_revision_pk']
        if 'parent_pk' in self.kwargs:
            initial['parent'] = self.kwargs['parent_pk']
        return initial

    def form_valid(self, form):
        self.object = form.save()

        if self.object.part.friendly_name:
            self.object.order = self.object.part.friendly_name
        else:
            self.object.order = self.object.part.name

        self.object.save()

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

    def get_success_url(self):
        return reverse('assemblies:ajax_assemblyparts_detail', args=(self.object.id, ))

# Update view for Assembly Part
class AssemblyPartAjaxUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = AssemblyPart
    form_class = AssemblyPartForm
    template_name='assemblies/ajax_assemblypart_form.html'
    context_object_name = 'assembly_part'
    permission_required = 'assemblies.add_assembly'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(AssemblyPartAjaxUpdateView, self).get_context_data(**kwargs)
        # Add Parts list to context to build form filter
        context.update({
            'part_types': PartType.objects.all(),
            'assembly_revision': self.object.assembly_revision,
            'builds': self.object.assembly_revision.builds.all()
        })
        if 'parent_pk' in self.kwargs:
            context.update({
                'parent': AssemblyPart.objects.get(id=self.kwargs['parent_pk'])
            })
        return context

    def get_form_kwargs(self):
        kwargs = super(AssemblyPartAjaxUpdateView, self).get_form_kwargs()
        if 'parent_pk' in self.kwargs:
            kwargs['parent_pk'] = self.kwargs['parent_pk']
        return kwargs

    def get_success_url(self):
        return reverse('assemblies:ajax_assemblyparts_detail', args=(self.object.id, ))

    def form_valid(self, form):
        # Get previous Part template object to check if it changed
        old_part_pk = self.object.tracker.previous('part')

        self.object = form.save()

        print(self.object.part.id)
        print(old_part_pk)

        if self.object.part.id != old_part_pk:
            # Need to check if there's Inventory on this AssemblyPart. If so, need to bump them off the Build
            if self.object.inventory.exists():
                for item in self.object.inventory.all():
                    item.detail = 'Removed from %s' % (item.build)
                    action_record = Action.objects.create(action_type='removefrombuild', detail=item.detail, location=item.location,
                                                          user=self.request.user, inventory=item)
                    item.build = None
                    item.assembly_part = None
                    item.parent = None
                    item.save()


        if self.object.part.friendly_name:
            self.object.order = self.object.part.friendly_name
        else:
            self.object.order = self.object.part.name

        self.object.save()

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response


class AssemblyPartAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = AssemblyPart
    context_object_name='assembly_part'
    template_name = 'assemblies/ajax_assemblypart_confirm_delete.html'
    permission_required = 'assemblies.change_assembly'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Need to check if there's Inventory on this AssemblyPart. If so, need to bump them off the Build
        if self.object.inventory.exists():
            for item in self.object.inventory.all():
                item.detail = 'Removed from %s' % (item.build)
                action_record = Action.objects.create(action_type='removefrombuild', detail=item.detail, location=item.location,
                                                      user=self.request.user, inventory=item)
                item.build = None
                item.assembly_part = None
                item.parent = None
                item.save()

        data = {
            'message': "Successfully submitted form data.",
            'object_type': self.object.get_object_type(),
            'parent_id': self.object.parent_id,
        }
        self.object.delete()
        return JsonResponse(data)


# Assembly Types Template Views

class AssemblyTypeListView(LoginRequiredMixin, ListView):
    model = AssemblyType
    template_name = 'assemblies/assembly_type_list.html'
    context_object_name = 'assembly_types'


class AssemblyTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = AssemblyType
    form_class = AssemblyTypeForm
    context_object_name = 'assembly_type'
    template_name = 'assemblies/assembly_type_form.html'
    permission_required = 'assemblies.add_assembly'
    redirect_field_name = 'home'

    def get_success_url(self):
        return reverse('assemblies:assembly_type_home', )

class AssemblyTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = AssemblyType
    form_class = AssemblyTypeForm
    context_object_name = 'assembly_type'
    template_name = 'assemblies/assembly_type_form.html'
    permission_required = 'assemblies.add_assembly'
    redirect_field_name = 'home'

    def get_success_url(self):
        return reverse('assemblies:assembly_type_home', )


class AssemblyTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    form_class = AssemblyTypeDeleteForm
    template_name = 'assemblies/assembly_type_confirm_delete.html'
    permission_required = 'assemblies.delete_assembly'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(AssemblyTypeDeleteView, self).get_context_data(**kwargs)
        assembly_type = AssemblyType.objects.get(id=self.kwargs['pk'])

        context.update({
            'assembly_type': assembly_type
        })
        return context

    def get_form_kwargs(self):
        kwargs = super(AssemblyTypeDeleteView, self).get_form_kwargs()
        if 'pk' in self.kwargs:
            kwargs['pk'] = self.kwargs['pk']
        return kwargs

    def form_valid(self, form):
        new_assembly_type = form.cleaned_data['new_assembly_type']
        assembly_type_to_delete = AssemblyType.objects.get(id=self.kwargs['pk'])

        # Need to check if there's Part Templates. If so, need move them to new Part Type.
        if assembly_type_to_delete.assemblies.exists():
            for assembly in assembly_type_to_delete.assemblies.all():
                assembly.assembly_type = new_assembly_type
                assembly.save()

        # Delete the Assembly object
        assembly_type_to_delete.delete()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assemblies:assembly_type_home')


# Direct Detail view for Assembly Types
class AssemblyTypeDetailView(LoginRequiredMixin, DetailView):
    model = AssemblyType
    context_object_name = 'assembly_type'
    template_name='assemblies/assembly_type_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AssemblyTypeDetailView, self).get_context_data(**kwargs)
        context.update({
            'node_type': 'assemblytype'
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# AJAX Views
class AssemblyTypeAjaxDetailView(LoginRequiredMixin, DetailView):
    model = AssemblyType
    context_object_name = 'assembly_type'
    template_name='assemblies/ajax_assembly_type_detail.html'
    redirect_field_name = 'home'
