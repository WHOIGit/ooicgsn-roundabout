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
from .forms import InventoryTestForm, InventoryTestResultForm
from .utils import _create_action_history
from common.util.mixins import AjaxFormMixin


def _reset_all_tests(inventory_item, user):
    # reset is_current status for older Test Results for this item
    results = inventory_item.test_results.filter(is_current=True)

    if results.exists():
        for result in results:
            result.is_current = False
            result.save()
            # create new Test Result to set Test to Unknown
            new_result = InventoryTestResult.objects.create(
                result=InventoryTestResult.UNKNOWN,
                inventory=inventory_item,
                inventory_test=result.inventory_test,
                is_current=True,
                user=user,
                notes="Test reset to Unknown status",
            )
            # Call the function to create an Action history chain for this event
            _create_action_history(inventory_item, Action.TEST, user)
    return True


"""
Test CBV Views
"""


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


class InventoryTestResultAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = InventoryTestResult
    form_class = InventoryTestResultForm
    context_object_name = "test_result"
    template_name = "inventory/ajax_test_result_form.html"

    def get_context_data(self, **kwargs):
        context = super(InventoryTestResultAjaxCreateView, self).get_context_data(
            **kwargs
        )
        inventory_item = Inventory.objects.get(id=self.kwargs["inventory_pk"])
        test_pk = self.kwargs.get("test_pk", None)

        if test_pk:
            test_result = InventoryTestResult.objects.get(id=test_pk)
        else:
            test_result = None

        context.update({"inventory_item": inventory_item, "test_result": test_result})
        return context

    def get_initial(self):
        inventory_item = Inventory.objects.get(id=self.kwargs["inventory_pk"])
        test_pk = self.kwargs.get("test_pk", None)
        if test_pk:
            test_result = InventoryTestResult.objects.get(id=test_pk)
            inventory_test_id = test_result.inventory_test.id
            result = test_result.result
        else:
            inventory_test_id = None
            result = None
        return {
            "inventory": inventory_item.id,
            "inventory_test": inventory_test_id,
            "result": result,
        }

    def form_valid(self, form):
        inventory_item = Inventory.objects.get(id=self.kwargs["inventory_pk"])

        # reset is_current status for older Test Results for this Test type
        old_results = inventory_item.test_results.filter(
            is_current=True, inventory_test=form.cleaned_data["inventory_test"]
        )
        for result in old_results:
            result.is_current = False
            result.save()

        self.object = form.save()
        self.object.is_current = True
        self.object.user = self.request.user
        self.object.save()

        # Call the function to create an Action history chain this event
        _create_action_history(inventory_item, Action.TEST, self.request.user)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                "message": "Successfully submitted form data.",
                "object_id": self.object.inventory_id,
                "object_type": self.object.inventory.get_object_type(),
                "detail_path": self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse(
            "inventory:ajax_inventory_detail", args=(self.object.inventory_id,)
        )


class InventoryTestResetAllActionView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        try:
            inventory_item = Inventory.objects.get(id=self.kwargs["inventory_pk"])
            _reset_all_tests(inventory_item, self.request.user)
        except Inventory.DoesNotExist:
            pass

        print(self.kwargs["inventory_pk"])
        return reverse(
            "inventory:ajax_inventory_detail", args=(self.kwargs["inventory_pk"],)
        )
