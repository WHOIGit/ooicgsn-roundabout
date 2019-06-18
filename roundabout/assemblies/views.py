from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import Assembly, AssemblyPart, AssemblyDocument
from .forms import AssemblyForm
from common.util.mixins import AjaxFormMixin

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
