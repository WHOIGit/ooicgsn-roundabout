from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .forms import UserDefinedFieldForm
from .models import Field

# UDF functionality

class UserDefinedFieldListView(LoginRequiredMixin, ListView):
    model = Field
    template_name = 'field_list.html'
    context_object_name = 'fields'


class UserDefinedFieldCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Field
    form_class = UserDefinedFieldForm
    context_object_name = 'field'
    permission_required = 'userdefinedfields.add_field'
    redirect_field_name = 'home'

    def get_success_url(self):
        return reverse('userdefinedfields:fields_home', )


class UserDefinedFieldUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Field
    form_class = UserDefinedFieldForm
    context_object_name = 'field'
    permission_required = 'userdefinedfields.add_printer'
    redirect_field_name = 'home'

    def get_success_url(self):
        return reverse('userdefinedfields:fields_home', )


class UserDefinedFieldDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Field
    success_url = reverse_lazy('userdefinedfields:fields_home')
    permission_required = 'userdefinedfields.delete_field'
    redirect_field_name = 'home'
