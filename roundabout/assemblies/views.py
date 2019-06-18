from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import Assembly, AssemblyPart, AssemblyDocument

# Load the javascript navtree 
def load_assemblies_navtree(request):
    assemblies = Assembly.objects.prefetch_related('assembly_parts')
    return render(request, 'assemblies/ajax_assembly_navtree.html', {'assemblies': assemblies})

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
            'assemblies': Assembly.objects.all(),
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
