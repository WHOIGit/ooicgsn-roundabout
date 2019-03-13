from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .forms import PrinterForm
from .models import Printer

# Create your views here.

class PrinterListView(LoginRequiredMixin, ListView):
    model = Printer
    template_name = 'printer_list.html'
    context_object_name = 'printers'


class PrinterCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Printer
    form_class = PrinterForm
    context_object_name = 'printer'
    permission_required = 'admintools.add_printer'
    redirect_field_name = 'home'

    def get_success_url(self):
        return reverse('admintools:printers_home', )
