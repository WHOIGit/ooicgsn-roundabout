from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import MooringPart
from .forms import MooringForm, MooringCopyLocationForm
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType
from common.util.mixins import AjaxFormMixin

# Mixins
# ------------------------------------------------------------------------------

class MooringsNavTreeMixin(LoginRequiredMixin, PermissionRequiredMixin, object):
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(MooringsNavTreeMixin, self).get_context_data(**kwargs)
        context.update({
            'locations': Location.objects.prefetch_related('mooring_parts__part__part_type')
        })
        return context


# General functions for use in Mooring views
# ------------------------------------------------------------------------------

# Makes a copy of the tree starting at "root_part", move to new Location, reparenting it to "parent"
def make_tree_copy(root_part, new_location, parent=None):
    #if parent:
        # re-read so django-mptt fields get updated
        #parent = MooringPart.objects.get(id=parent.id)
    new_mp = MooringPart.objects.create(location=new_location, part=root_part.part, parent=parent, order=root_part.order)

    for child in root_part.get_children():
        make_tree_copy(child, new_location, new_mp)


# AJAX functions for Forms and Navtree
# ------------------------------------------------------------------------------

# Main Navtree function
def load_moorings_navtree(request):
    # Temporary hack to limit Locations, need to fix
    locations = Location.objects.exclude(name='Trash Bin').exclude(name='Retired').exclude(name='Snapshots').prefetch_related('mooring_parts__part__part_type')
    return render(request, 'moorings/ajax_mooring_navtree.html', {'locations': locations})


# Filter Navtree by Part Type function
def filter_moorings_navtree(request):
    part_types = request.GET.getlist('part_types[]')
    part_types = list(map(int, part_types))
    locations = Location.objects.exclude(name='Trash Bin').exclude(name='Retired').exclude(name='Snapshots').prefetch_related('mooring_parts__part__part_type')
    return render(request, 'moorings/ajax_mooring_navtree.html', {'locations': locations, 'part_types': part_types})


# Function to load Parts based on Part Type filter
def load_part_templates(request):
    part_type = request.GET.get('part_type')
    if part_type == 'All':
        part_list = Part.objects.all()
    else:
        part_list = Part.objects.filter(part_type=part_type)
    return render(request, 'inventory/part_templates_dropdown_list_options.html', {'parts': part_list})


# Function to load available Mooring Parts based on Location
def load_mooring_parts(request):
    location_id = request.GET.get('location')
    mooring_parts_list = MooringPart.objects.none()
    if location_id:
        location = Location.objects.get(id=location_id)
        mooring_parts_list = MooringPart.objects.filter(location=location).prefetch_related('part')
    return render(request, 'inventory/mooringparts_dropdown_list_options.html', {'mooring_parts': mooring_parts_list})


# Mooring CBV Views for CRUD operations and menu Actions
# ------------------------------------------------------------------------------
# AJAX Views

class MooringsAjaxDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = MooringPart
    context_object_name = 'mooring_part'
    template_name='moorings/ajax_mooring_detail.html'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'


class MooringsAjaxLocationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Location
    context_object_name = 'location'
    template_name='moorings/ajax_mooring_location_detail.html'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'


class MooringsAjaxCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = MooringPart
    form_class = MooringForm
    template_name='moorings/ajax_mooring_form.html'
    context_object_name = 'mooring_part'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(MooringsAjaxCreateView, self).get_context_data(**kwargs)
        # Add Parts list to context to build form filter
        context.update({
            'part_types': PartType.objects.all()
        })
        if 'parent_pk' in self.kwargs:
            context.update({
                'parent': MooringPart.objects.get(id=self.kwargs['parent_pk'])
            })
        return context

    def get_form_kwargs(self):
        kwargs = super(MooringsAjaxCreateView, self).get_form_kwargs()
        if 'parent_pk' in self.kwargs:
            kwargs['parent_pk'] = self.kwargs['parent_pk']
        if 'current_location' in self.kwargs:
            kwargs['current_location'] = self.kwargs['current_location']
        return kwargs

    def get_initial(self):
        #Returns the initial data to use for forms on this view.
        initial = super(MooringsAjaxCreateView, self).get_initial()
        if 'parent_pk' in self.kwargs:
            initial = super(MooringsAjaxCreateView, self).get_initial()
            initial['parent'] = self.kwargs['parent_pk']
            initial['location'] = self.kwargs['current_location']
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
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse('moorings:ajax_moorings_detail', args=(self.object.id, ))


class MooringsAjaxUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = MooringPart
    form_class = MooringForm
    template_name='moorings/ajax_mooring_form.html'
    context_object_name = 'mooring_part'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(MooringsAjaxUpdateView, self).get_context_data(**kwargs)
        # Add Parts list to context to build form filter
        context.update({
            'part_types': PartType.objects.all()
        })
        if 'parent_pk' in self.kwargs:
            context.update({
                'parent': MooringPart.objects.get(id=self.kwargs['parent_pk'])
            })
        return context

    def get_form_kwargs(self):
        kwargs = super(MooringsAjaxUpdateView, self).get_form_kwargs()
        if 'parent_pk' in self.kwargs:
            kwargs['parent_pk'] = self.kwargs['parent_pk']
        if 'current_location' in self.kwargs:
            kwargs['current_location'] = self.kwargs['current_location']
        return kwargs

    def get_success_url(self):
        return reverse('moorings:ajax_moorings_detail', args=(self.object.id, ))

    def form_valid(self, form):
        self.object = form.save()

        if self.object.part.friendly_name:
            self.object.order = self.object.part.friendly_name
        else:
            self.object.order = self.object.part.name

        self.object.save()

        if self.object.get_descendants():
            children = self.object.get_descendants()
            for child in children:
                child.location_id = self.object.location_id
                child.save()

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


class MooringsAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = MooringPart
    context_object_name='mooring_part'
    template_name = 'moorings/ajax_mooring_confirm_delete.html'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.parent_id,
        }
        self.object.delete()
        return JsonResponse(data)


# Views to copy template at Assembly level -- PLACEHOLDERS NOT OPERATIONAL
class MooringsCopyAssemblyView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'moorings/ajax_mooring_form.html'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'


# View to copy full Mooring Templates by location
class MooringsCopyLocationView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, FormView):
    form_class = MooringCopyLocationForm
    template_name = 'moorings/ajax_mooring_location_copy_form.html'
    context_object_name = 'location'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(MooringsCopyLocationView, self).get_context_data(**kwargs)
        context.update({
            'location': Location.objects.get(id=self.kwargs['pk'])
        })
        return context

    def get_form_kwargs(self):
        kwargs = super(MooringsCopyLocationView, self).get_form_kwargs()
        if 'pk' in self.kwargs:
            kwargs['pk'] = self.kwargs['pk']
        return kwargs

    def get_success_url(self):
        return reverse('moorings:ajax_moorings_location_detail', args=(self.kwargs['pk'], ))

    def form_valid(self, form, **kwargs):
        current_location = Location.objects.get(pk=self.kwargs['pk'])
        new_location = form.cleaned_data.get('location')
        mooring_parts = current_location.mooring_parts.all()

        for mp in mooring_parts:
            if mp.is_root_node():
                make_tree_copy(mp, new_location, mp.parent)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': new_location.id,
            }
            return JsonResponse(data)
        else:
            return response


# Base non-AJAX views for direct links and fallback

class MooringsDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = MooringPart
    template_name = 'moorings/mooring_detail.html'
    context_object_name = 'mooring_part'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(MooringsDetailView, self).get_context_data(**kwargs)
        context.update({
            'part_types': PartType.objects.all(),
            'node_type': 'moorings'
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class MooringsHomeView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'moorings/mooring_list.html'
    context_object_name = 'mooring_parts'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(MooringsHomeView, self).get_context_data(**kwargs)
        context.update({
            'part_types': PartType.objects.all(),
            'node_type': 'moorings'
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# For testing navtree load speed queries
class MooringsHomeTestView(MooringsNavTreeMixin, TemplateView):
    template_name = 'moorings/mooring_list_test.html'
    context_object_name = 'mooring_parts'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(MooringsHomeTestView, self).get_context_data(**kwargs)
        context.update({
            'node_type': 'mooring_part'
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class MooringsCreateView(MooringsNavTreeMixin, CreateView):
    model = MooringPart
    form_class = MooringForm
    template_name='moorings/mooring_form.html'
    context_object_name = 'mooring_part'

    def get_context_data(self, **kwargs):
        context = super(MooringsCreateView, self).get_context_data(**kwargs)
        # Add Parts list to context to build form filter
        context.update({
            'part_types': PartType.objects.all()
        })
        if 'parent_pk' in self.kwargs:
            context.update({
                'parent': MooringPart.objects.get(id=self.kwargs['parent_pk'])
            })
        return context

    def get_form_kwargs(self):
        kwargs = super(MooringsCreateView, self).get_form_kwargs()
        if 'parent_pk' in self.kwargs:
            kwargs['parent_pk'] = self.kwargs['parent_pk']
        if 'current_location' in self.kwargs:
            kwargs['current_location'] = self.kwargs['current_location']
        return kwargs

    def get_initial(self):
        #Returns the initial data to use for forms on this view.
        initial = super(MooringsCreateView, self).get_initial()
        if 'parent_pk' in self.kwargs:
            initial = super(MooringsCreateView, self).get_initial()
            initial['parent'] = self.kwargs['parent_pk']
            initial['location'] = self.kwargs['current_location']
        return initial

    def get_success_url(self):
        return reverse('moorings:moorings_detail', args=(self.object.id, self.object.location_id))


class MooringsUpdateView(MooringsNavTreeMixin, UpdateView):
    model = MooringPart
    form_class = MooringForm
    template_name='moorings/mooring_form.html'
    context_object_name = 'mooring_part'

    def get_context_data(self, **kwargs):
        context = super(MooringsUpdateView, self).get_context_data(**kwargs)
        # Add Parts list to context to build form filter
        context.update({
            'part_types': PartType.objects.all()
        })
        if 'parent_pk' in self.kwargs:
            context.update({
                'parent': MooringPart.objects.get(id=self.kwargs['parent_pk'])
            })
        return context

    def get_success_url(self):
        return reverse('moorings:moorings_detail', args=(self.object.id, self.object.location_id))


class MooringsSubassemblyAddView(MooringsNavTreeMixin, CreateView):
    model = MooringPart
    form_class = MooringForm
    template_name='moorings/mooring_form.html'
    context_object_name = 'mooring_part'

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


class MooringsDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = MooringPart
    template_name='moorings/mooring_confirm_delete.html'
    success_url = reverse_lazy('moorings:moorings_home')
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'
