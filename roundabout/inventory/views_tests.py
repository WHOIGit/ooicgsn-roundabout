from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import (
    View,
    DetailView,
    ListView,
    RedirectView,
    UpdateView,
    CreateView,
    DeleteView,
    TemplateView,
    FormView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import (
    Inventory,
    InventoryTest,
    InventoryTestResult,
    Action,
)
from .forms import InventoryTestForm


# Test Template Views


class InventoryTestListView(LoginRequiredMixin, ListView):
    model = InventoryTest
    template_name = "inventory/test_list.html"
    context_object_name = "tests"


class InventoryTestCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = InventoryTest
    form_class = InventoryTestForm
    context_object_name = "test"
    template_name = "inventory/test_form.html"
    permission_required = "parts.add_part"
    redirect_field_name = "home"

    def get_success_url(self):
        return reverse(
            "inventory:test_home",
        )


class InventoryTestUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = InventoryTest
    form_class = InventoryTestForm
    context_object_name = "test"
    template_name = "inventory/test_form.html"
    permission_required = "parts.add_part"
    redirect_field_name = "home"

    def get_success_url(self):
        return reverse(
            "inventory:test_home",
        )


class InventoryTestDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = InventoryTest
    success_url = reverse_lazy("inventory:test_home")
    permission_required = "parts.delete_part"
    template_name = "inventory/test_confirm_delete.html"
    redirect_field_name = "home"


# Direct detail view
class InventoryTestDetailView(LoginRequiredMixin, DetailView):
    model = InventoryTest
    template_name = "inventory/test_detail.html"
    context_object_name = "test"

    def get_context_data(self, **kwargs):
        context = super(InventoryTestDetailView, self).get_context_data(**kwargs)
        context.update({"node_type": "test"})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# AJAX Views


class InventoryTestAjaxDetailView(LoginRequiredMixin, DetailView):
    model = InventoryTest
    context_object_name = "test"
    template_name = "inventory/ajax_test_detail.html"
    redirect_field_name = "home"
