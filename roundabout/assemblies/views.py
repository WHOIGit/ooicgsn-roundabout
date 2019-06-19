from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import Assembly, AssemblyPart, AssemblyType, AssemblyDocument
from .forms import AssemblyForm, AssemblyPartForm
from roundabout.parts.models import PartType
from common.util.mixins import AjaxFormMixin

# Load the javascript navtree
def load_assemblies_navtree(request):
    assembly_types = AssemblyType.objects.prefetch_related('assemblies__assembly_parts')
    assemblies = Assembly.objects.prefetch_related('assembly_parts')
    return render(request, 'assemblies/ajax_assembly_navtree.html', {'assembly_types': assembly_types})

## CBV views for Assembly app ##

# Landing page for assemblies
class AssemblyHomeView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'assemblies/assembly_list.html'
    context_object_name = 'assemblies'
    permission_required = 'moorings.add_mooringpart'
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


# Detail view for assemblies
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
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def form_valid(self, form):
        self.object = form.save()

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
        return reverse('assemblies:ajax_assemblies_detail', args=(self.object.id,))


# Update view for assemblies
class AssemblyAjaxUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = Assembly
    form_class = AssemblyForm
    context_object_name = 'assembly'
    template_name='assemblies/ajax_assembly_form.html'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def form_valid(self, form):
        self.object = form.save()

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
        return reverse('assemblies:ajax_assemblies_detail', args=(self.object.id,))


class AssemblyAjaxDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Assembly
    template_name = 'assemblies/ajax_assembly_confirm_delete.html'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.id,
        }
        self.object.delete()

        return JsonResponse(data)


### CBV views for AssemblyPart model ###

# Detail view for Assembly Part
class AssemblyPartAjaxDetailView(LoginRequiredMixin, DetailView):
    model = AssemblyPart
    context_object_name = 'assembly_part'
    template_name='assemblies/ajax_assemblypart_detail.html'


# Create view for Assembly Part
class AssemblyPartAjaxCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = AssemblyPart
    form_class = AssemblyPartForm
    template_name='assemblies/ajax_assemblypart_form.html'
    context_object_name = 'assembly_part'
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(AssemblyPartAjaxCreateView, self).get_context_data(**kwargs)

        context.update({
            'part_types': PartType.objects.all(),
            'assembly': Assembly.objects.get(id=self.kwargs['assembly_pk'])
        })
        if 'parent_pk' in self.kwargs:
            context.update({
                'parent': AssemblyPart.objects.get(id=self.kwargs['parent_pk'])
            })
        return context

    def get_form_kwargs(self):
        kwargs = super(AssemblyPartAjaxCreateView, self).get_form_kwargs()
        kwargs['assembly_pk'] = self.kwargs['assembly_pk']
        if 'parent_pk' in self.kwargs:
            kwargs['parent_pk'] = self.kwargs['parent_pk']
        return kwargs

    def get_initial(self):
        #Returns the initial data to use for forms on this view.
        initial = super(AssemblyPartAjaxCreateView, self).get_initial()
        initial['assembly'] = self.kwargs['assembly_pk']
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
    permission_required = 'moorings.add_mooringpart'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super(AssemblyPartAjaxUpdateView, self).get_context_data(**kwargs)
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
        kwargs = super(AssemblyPartAjaxUpdateView, self).get_form_kwargs()
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
