from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError

from .models import Part, PartType
from .forms import PartForm, DocumentationFormset, PartSubassemblyAddForm, PartSubassemblyEditForm
from roundabout.locations.models import Location
from common.util.mixins import AjaxFormMixin

import re

# Mixins

class PartsNavTreeMixin(LoginRequiredMixin, PermissionRequiredMixin, object):
    permission_required = 'parts.add_part'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(PartsNavTreeMixin, self).get_context_data(**kwargs)
        context.update({
            'part_types': PartType.objects.prefetch_related('parts')
        })
        return context


# AJAX Views

# Function to validate Part Number from AJAX request
def validate_part_number(request):
    part_number = request.GET.get('part_number')
    form_action = request.GET.get('form_action')
    initial_part_number = request.GET.get('initial_part_number')
    part = Part.objects.filter(part_number=part_number).first()

    if part:
        if part.part_number == str(initial_part_number):
            is_error = False
            error_message = ''
        else:
            is_error = True
            error_message = 'Part Number already in use! Part Number must be unique'
    else:
        is_error = False
        error_message = ''

    """
    else:
        if not re.match(r'^[a-zA-Z0-9_]{4}-[a-zA-Z0-9_]{5}-[a-zA-Z0-9_]{5}$', part_number):
            is_error = True
            error_message = 'Part Number in wrong format. Must be ####-#####-#####'
        else:
            is_error = False
            error_message = ''
    """

    data = {
        'is_error': is_error,
        'error_message': error_message,
    }
    return JsonResponse(data)


# Part Template Views

def load_parts_navtree(request):
    part_types = PartType.objects.prefetch_related('parts')
    return render(request, 'parts/ajax_part_navtree.html', {'part_types': part_types})


class PartsAjaxDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Part
    context_object_name = 'part_template'
    template_name='parts/ajax_part_detail.html'
    permission_required = 'parts.add_part'
    redirect_field_name = 'home'


class PartsAjaxCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = Part
    form_class = PartForm
    context_object_name = 'part_template'
    template_name='parts/ajax_part_form.html'
    permission_required = 'parts.add_part'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = DocumentationFormset(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = DocumentationFormset(
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
        return reverse('parts:ajax_parts_detail', args=(self.object.id, ))


class PartsAjaxUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = Part
    form_class = PartForm
    context_object_name = 'part_template'
    template_name='parts/ajax_part_form.html'
    permission_required = 'parts.add_part'
    redirect_field_name = 'home'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = DocumentationFormset(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = DocumentationFormset(
            self.request.POST, instance=self.object)

        if (form.is_valid() and documentation_form.is_valid()):
            return self.form_valid(form, documentation_form)
        return self.form_invalid(form, documentation_form)

    def form_valid(self, form, documentation_form):
        part_form = form.save()
        self.object = part_form
        documentation_form.instance = self.object
        documentation_form.save()
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

    def form_invalid(self, form, documentation_form):
        form_errors = documentation_form.errors

        if self.request.is_ajax():
            data = form.errors
            return JsonResponse(data, status=400)
        else:
            return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form, form_errors=form_errors))

    def get_success_url(self):
        return reverse('parts:ajax_parts_detail', args=(self.object.id, ))


class PartsAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Part
    context_object_name='part_template'
    template_name = 'parts/ajax_part_confirm_delete.html'
    permission_required = 'parts.add_part'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.part_type_id,
        }
        self.object.delete()
        return JsonResponse(data)


# Base Views

class PartsDetailView(LoginRequiredMixin, DetailView):
    model = Part
    template_name = 'parts/part_detail.html'
    context_object_name = 'part_template'

    def get_context_data(self, **kwargs):
        context = super(PartsDetailView, self).get_context_data(**kwargs)
        context.update({
            'node_type': 'parts'
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PartsHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'parts/part_list.html'

    def get_context_data(self, **kwargs):
        context = super(PartsHomeView, self).get_context_data(**kwargs)
        context.update({
            'node_type': 'parts'
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PartsCreateView(PartsNavTreeMixin, CreateView):
    model = Part
    form_class = PartForm
    context_object_name = 'part_template'

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = DocumentationFormset(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = DocumentationFormset(
            self.request.POST, instance=self.object)

        if (form.is_valid() and documentation_form.is_valid()):
            return self.form_valid(form, documentation_form)
        return self.form_invalid(form, documentation_form)

    def form_valid(self, form, documentation_form):
        self.object = form.save()
        documentation_form.instance = self.object
        documentation_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, documentation_form):
        form_errors = documentation_form.errors
        return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form, form_errors=form_errors))

    def get_success_url(self):
        return reverse('parts:parts_detail', args=(self.object.id, ))


class PartsUpdateView(PartsNavTreeMixin, UpdateView):
    model = Part
    form_class = PartForm
    context_object_name = 'part_template'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = DocumentationFormset(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = DocumentationFormset(
            self.request.POST, instance=self.object)

        if (form.is_valid() and documentation_form.is_valid()):
            return self.form_valid(form, documentation_form)
        return self.form_invalid(form, documentation_form)

    def form_valid(self, form, documentation_form):
        part_form = form.save()
        self.object = part_form
        documentation_form.instance = self.object
        documentation_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, documentation_form):
        return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form))

    def get_success_url(self):
        return reverse('parts:parts_detail', args=(self.object.id, ))


class PartsSubassemblyAddView(PartsNavTreeMixin, CreateView):
    model = Part
    form_class = PartForm
    context_object_name = 'part_template'
    template_name = 'parts/part_form.html'

    def get_context_data(self, **kwargs):
        context = super(PartsSubassemblyAddView, self).get_context_data(**kwargs)
        context.update({
            'parent': Part.objects.get(id=self.kwargs['pk'])
        })
        return context

    def get_initial(self):
        #Returns the initial data to use for forms on this view.
        initial = super(PartsSubassemblyAddView, self).get_initial()
        initial['parent'] = self.kwargs['pk']
        initial['location'] = self.kwargs['current_location']
        return initial

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = DocumentationFormset(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        documentation_form = DocumentationFormset(
            self.request.POST, instance=self.object)

        if (form.is_valid() and documentation_form.is_valid()):
            return self.form_valid(form, documentation_form)
        return self.form_invalid(form, documentation_form)

    def form_valid(self, form, documentation_form):
        self.object = form.save()
        documentation_form.instance = self.object
        documentation_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, documentation_form):
        form_errors = documentation_form.errors
        return self.render_to_response(self.get_context_data(form=form, documentation_form=documentation_form, form_errors=form_errors))

    def get_success_url(self):
        return reverse('parts:parts_detail', args=(self.object.id, self.kwargs['current_location']))


class PartsSubassemblyEditView(PartsNavTreeMixin, UpdateView):
    model = Part
    form_class = PartSubassemblyEditForm
    context_object_name = 'part_template'
    template_name = 'parts/part_form_subassembly.html'

    def get_context_data(self, **kwargs):
        context = super(PartsSubassemblyEditView, self).get_context_data(**kwargs)
        context.update({
            'parent': Part.objects.get(id=self.kwargs['parent_pk'])
        })
        return context

    def get_success_url(self):
        return reverse('parts:parts_detail', args=(self.object.id, self.kwargs['current_location']))


class PartsSubassemblyAvailableView(PartsNavTreeMixin, DetailView):
    model = Part
    template_name = 'parts/part_subassembly_existing.html'
    context_object_name = 'parent'

    def get_context_data(self, **kwargs):
        context = super(PartsSubassemblyAvailableView, self).get_context_data(**kwargs)

        context.update({
            'parts': Part.objects.filter(parent=context['parent'])
        })
        return context


class PartsSubassemblyActionView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        subassembly = get_object_or_404(Part, pk=kwargs['pk'])
        new_location = get_object_or_404(Location, pk=kwargs['current_location'])
        subassembly.location.add(new_location)

        return reverse('parts:parts_detail', args=(self.kwargs['parent_pk'], self.kwargs['current_location']) ) + '#subassemblies'


class PartsDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Part
    success_url = reverse_lazy('parts:parts_list')
    permission_required = 'parts.add_part'
    redirect_field_name = 'home'

    def get_success_url(self):
        if self.kwargs.get('parent_pk'):
            return reverse('parts:parts_detail', args=(self.kwargs['parent_pk'], self.kwargs['current_location']))
        else:
            return reverse_lazy('parts:parts_list')


# Part Types Template Views

# AJAX Views

class PartsTypeAjaxDetailView(LoginRequiredMixin , DetailView):
    model = PartType
    context_object_name = 'part_type'
    template_name='parts/ajax_part_type_detail.html'
    redirect_field_name = 'home'
