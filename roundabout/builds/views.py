from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from common.util.mixins import AjaxFormMixin
from .models import Build, BuildAction
from .forms import *
from roundabout.locations.models import Location

# Load the javascript navtree
def load_builds_navtree(request):
    locations = Location.objects.exclude(root_type='Retired').prefetch_related('builds').prefetch_related('inventory__part__part_type')
    return render(request, 'builds/ajax_build_navtree.html', {'locations': locations})

## CBV views for Builds app ##

# Landing page for Builds
class BuildHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'builds/build_list.html'
    context_object_name = 'builds'

    def get_context_data(self, **kwargs):
        context = super(BuildHomeView, self).get_context_data(**kwargs)
        context.update({
            'node_type': 'builds',
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# Detail view for builds
class BuildAjaxDetailView(LoginRequiredMixin, DetailView):
    model = Build
    context_object_name = 'build'
    template_name='builds/ajax_build_detail.html'


# Create view for assemblies
class BuildAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Build
    form_class = BuildForm
    context_object_name = 'build'
    template_name='builds/ajax_build_form.html'

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
        return reverse('builds:ajax_builds_detail', args=(self.object.id,))
