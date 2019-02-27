from django.shortcuts import render
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import Printer

# Create your views here.

class PrinterListView(LoginRequiredMixin, ListView):
    model = Printer
    template_name = 'printer_list.html'
    context_object_name = 'printers'
