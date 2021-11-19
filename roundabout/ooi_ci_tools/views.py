"""
# Copyright (C) 2019-2020 Woods Hole Oceanographic Institution
#
# This file is part of the Roundabout Database project ("RDB" or
# "ooicgsn-roundabout").
#
# ooicgsn-roundabout is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# ooicgsn-roundabout is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ooicgsn-roundabout in the COPYING.md file at the project root.
# If not, see <http://www.gnu.org/licenses/>.
"""

import csv
import io
import re
from decimal import Decimal

from dateutil import parser
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils.timezone import make_aware
from django.views.generic import TemplateView, FormView
from common.util.mixins import AjaxFormMixin
from django.views.generic import CreateView, UpdateView, DeleteView

from roundabout.cruises.models import Cruise, Vessel
from roundabout.assemblies.models import Assembly
from roundabout.configs_constants.models import ConfigDefault, ConfigEvent, ConfigName, ConfigValue
from roundabout.builds.models import Build
from roundabout.locations.models import Location
from roundabout.inventory.models import Inventory, Action, Deployment, InventoryDeployment
from roundabout.inventory.utils import _create_action_history
from roundabout.calibrations.utils import handle_reviewers, user_ccc_reviews
from roundabout.calibrations.tasks import check_events
from .forms import *
from .models import *
from .tasks import *
# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels
labels = set_app_labels()

# Obtain file processing percent total
def upload_status(request):
    result = cache.get('validation_progress')
    cache.delete('validation_progress')
    return JsonResponse({
        'progress': result,
    })

# Deployment CSV Importer
def import_deployments(csv_files):
    cache.set('dep_files',csv_files, timeout=None)
    job = parse_deployment_files.delay()


# Cruise CSV Importer
def import_cruises(cruises_files):
    cache.set('cruises_files', cruises_files, timeout=None)
    job = parse_cruise_files.delay()

# Vessel CSV Importer
def import_vessels(vessels_files):
    cache.set('vessels_files', vessels_files, timeout=None)
    job = parse_vessel_files.delay()

# Reference Designator CSV Importer
def import_refdes(refdes_files):
    cache.set('refdes_files', refdes_files, timeout=None)
    job = parse_refdes_files.delay()

# Bulk Upload CSV Importer
def import_bulk(bulk_files):
    cache.set('bulk_files', bulk_files, timeout=None)
    job = parse_bulk_files.delay()

# Calibration CSV Importer
def import_calibrations(cal_files, user_draft):
    csv_files = []
    ext_files = []
    for file in cal_files:
        ext = file.name[-3:]
        if ext == 'ext':
            ext_files.append(file)
        if ext == 'csv':
            csv_files.append(file)
    cache.set('user_draft', user_draft, timeout=None)
    cache.set('ext_files', ext_files, timeout=None)
    cache.set('csv_files', csv_files, timeout=None)
    job = parse_cal_files.delay()
    cache.set('import_task', job.task_id, timeout=None)

# CSV Importer View
# Activates parsing tasks based on selected files
def import_csv(request):
    confirm = ""
    if not ImportConfig.objects.exists():
        ImportConfig.objects.create()
    if request.method == "POST":
        cal_form = ImportCalibrationForm(request.POST, request.FILES)
        dep_form = ImportDeploymentsForm(request.POST, request.FILES)
        cruises_form = ImportCruisesForm(request.POST, request.FILES)
        vessels_form = ImportVesselsForm(request.POST, request.FILES)
        refdes_form = ImportReferenceDesignatorForm(request.POST, request.FILES)
        bulk_form = ImportBulkUploadForm(request.POST, request.FILES)
        cal_files = request.FILES.getlist('calibration_csv')
        dep_files = request.FILES.getlist('deployments_csv')
        cruises_file = request.FILES.getlist('cruises_csv')
        vessels_file = request.FILES.getlist('vessels_csv')
        refdes_file = request.FILES.getlist('refdes_csv')
        bulk_file = request.FILES.getlist('bulk_csv')
        cache.set('user', request.user, timeout=None)
        if cal_form.is_valid() and len(cal_files) >= 1:
            import_calibrations(cal_files, cal_form.cleaned_data['user_draft'])
            confirm = "True"
        if dep_form.is_valid() and len(dep_files) >= 1:
            import_deployments(dep_files)
            confirm = "True"
        if cruises_form.is_valid() and len(cruises_file) >= 1:
            import_cruises(cruises_file)
            confirm = "True"
        if vessels_form.is_valid() and len(vessels_file) >= 1:
            import_vessels(vessels_file)
            confirm = "True"
        if refdes_form.is_valid() and len(refdes_file) >= 1:
            import_refdes(refdes_file)
            confirm = "True"
        if bulk_form.is_valid() and len(bulk_file) >= 1:
            import_bulk(bulk_file)
            confirm = "True"
    else:
        cal_form = ImportCalibrationForm()
        dep_form = ImportDeploymentsForm()
        cruises_form = ImportCruisesForm()
        vessels_form = ImportVesselsForm()
        refdes_form = ImportReferenceDesignatorForm()
        bulk_form = ImportBulkUploadForm()
    return render(request, 'ooi_ci_tools/import_tool.html', {
        "form": cal_form,
        'dep_form': dep_form,
        'cruises_form': cruises_form,
        'vessels_form': vessels_form,
        'refdes_form': refdes_form,
        'bulk_form': bulk_form,
        'confirm': confirm
    })


# Action-Comment View
def action_comment(request, pk):
    action = Action.objects.get(id=pk)
    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment_form.instance.action = action
            comment_form.instance.user = request.user
            comment_form.instance.detail = comment_form.cleaned_data['detail']
            comment_form.save()
    else:
        comment_form = CommentForm()
        comment_form.instance.action = action
        comment_form.instance.user = request.user
    return render(request, 'ooi_ci_tools/action_comment.html', {
        "comment_form": comment_form,
        "action_object": action
    })

# Sub-comment create view
def sub_comment(request, pk, crud=None):
    comment= MPTTComment.objects.get(id=pk)
    if request.method == "POST":
        if crud == 'add':
            comment_form = CommentForm(request.POST)
        else:
            comment_form = CommentForm(request.POST, instance=comment)
        if comment_form.is_valid():
            if crud == 'add':
                comment_form.instance.parent = comment
                comment_form.instance.action = comment.action
                comment_form.instance.user = request.user
                comment_form.instance.detail = comment_form.cleaned_data['detail']
            else:
                comment_form.instance.detail = comment_form.cleaned_data['detail']
            comment_form.save()
    else:
        if crud == 'add':
            comment_form = CommentForm()
        else:
            comment_form = CommentForm(instance=comment)
    return render(request, 'ooi_ci_tools/comment_comment.html', {
        "comment_form": comment_form,
        "parent_comment": comment
    })

# Comment delete view
class CommentDelete(LoginRequiredMixin, DeleteView):
    model = MPTTComment
    context_object_name='comment_obj'
    template_name = 'ooi_ci_tools/comment_delete.html'
    permission_required = 'ooi_ci_tools.add_comments'
    redirect_field_name = 'home'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'parent_id': self.object.id,
            'parent_type': 'comment',
            'object_type': self.object.get_object_type(),
        }
        self.object.delete()
        return JsonResponse(data)

    def get_success_url(self):
        return reverse_lazy('inventory:ajax_inventory_detail', args=(self.object.action.inventory.id, ))



# Handles import configurations of Calibration, Deployment, Cruises, and Vessels CSVs
class ImportConfigUpdate(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = ImportConfig
    form_class = ImportConfigForm
    context_object_name = 'import_config'
    template_name='ooi_ci_tools/import_config.html'

    def get(self, request, *args, **kwargs):
        if ImportConfig.objects.exists():
            self.object = self.get_object()
        else:
            self.object = ImportConfig.objects.create()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(
            self.get_context_data(
                form=form,
            )
        )

    def get_success_url(self):
        return reverse('ooi_ci_tools:import_csv')



# Handles Bulk Upload file edits for Inventory items
class InvBulkUploadEventUpdate(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = BulkUploadEvent
    form_class = BulkUploadEventForm
    context_object_name = 'event_template'
    template_name='ooi_ci_tools/bulkupload_edit.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        inv_id = self.kwargs['inv_id']
        file_name = self.kwargs['file']
        bulk_file = BulkFile.objects.get(file_name = file_name)
        file_records = BulkAssetRecord.objects.filter(bulk_file = bulk_file)
        bulk_file_form = EventAssetFileFormset(
            instance=self.object,
            queryset=file_records
        )
        return self.render_to_response(
            self.get_context_data(
                form=form,
                bulk_file_form=bulk_file_form,
                file_name=file_name,
                inv_id=inv_id
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        bulk_file_form = EventAssetFileFormset(
            self.request.POST,
            instance=self.object
        )
        if (form.is_valid() and bulk_file_form.is_valid()):
            return self.form_valid(form, bulk_file_form)
        return self.form_invalid(form, bulk_file_form)

    def form_valid(self, form, bulk_file_form):
        file_name = self.kwargs['file']
        form.instance.approved = False
        form.save()
        handle_reviewers(form)
        self.object = form.save()
        bulk_file_form.instance = self.object
        bulk_file_form.save()
        _create_action_history(self.object, Action.UPDATE, self.request.user, filename = file_name)
        job = check_events.delay()
        response = HttpResponseRedirect(self.get_success_url())
        if self.request.is_ajax():
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response


    def form_invalid(self, form, bulk_file_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(
                    data,
                    status=400,
                    safe=False
                )
            if bulk_file_form.errors:
                data = bulk_file_form.errors
                return JsonResponse(
                    data,
                    status=400,
                    safe=False
                )
            
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    bulk_file_form=bulk_file_form,
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        inv_id = self.kwargs['inv_id']
        return reverse('inventory:ajax_inventory_detail', args=(inv_id, ))



# Handles Bulk Upload file edits for Part items
class PartBulkUploadEventUpdate(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = BulkUploadEvent
    form_class = BulkUploadEventForm
    context_object_name = 'event_template'
    template_name='ooi_ci_tools/part_bulkupload_edit.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        file_name = self.kwargs['file']
        part_id = self.kwargs['part_id']
        bulk_file = BulkFile.objects.get(file_name = file_name)
        file_records = BulkVocabRecord.objects.filter(bulk_file = bulk_file)
        bulk_file_form = EventVocabFileFormset(
            instance=self.object,
            queryset=file_records
        )
        return self.render_to_response(
            self.get_context_data(
                form=form,
                bulk_file_form=bulk_file_form,
                file_name=file_name,
                part_id=part_id
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        bulk_file_form = EventVocabFileFormset(
            self.request.POST,
            instance=self.object
        )
        if (form.is_valid() and bulk_file_form.is_valid()):
            return self.form_valid(form, bulk_file_form)
        return self.form_invalid(form, bulk_file_form)

    def form_valid(self, form, bulk_file_form):
        form.instance.approved = False
        form.save()
        handle_reviewers(form)
        self.object = form.save()
        bulk_file_form.instance = self.object
        bulk_file_form.save()
        _create_action_history(self.object, Action.UPDATE, self.request.user)
        job = check_events.delay()
        response = HttpResponseRedirect(self.get_success_url())
        if self.request.is_ajax():
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'object_type': self.object.get_object_type(),
                'detail_path': self.get_success_url(),
            }
            return JsonResponse(data)
        else:
            return response


    def form_invalid(self, form, bulk_file_form):
        if self.request.is_ajax():
            if form.errors:
                data = form.errors
                return JsonResponse(
                    data,
                    status=400,
                    safe=False
                )
            if bulk_file_form.errors:
                data = bulk_file_form.errors
                return JsonResponse(
                    data,
                    status=400,
                    safe=False
                )
            
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    bulk_file_form=bulk_file_form,
                    form_errors=form_errors
                )
            )

    def get_success_url(self):
        part_id = self.kwargs['part_id']
        return reverse('parts:ajax_parts_detail', args=(part_id, ))

# Handles deletion of Inventory Bulk Upload Files
class InvBulkUploadEventDelete(LoginRequiredMixin, AjaxFormMixin, DeleteView):
    model = BulkUploadEvent
    context_object_name='event_template'
    template_name = 'ooi_ci_tools/bulkupload_delete.html'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inv_id'] = self.kwargs['inv_id']
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'object_type': 'bulk_upload_event',
        }
        self.object.delete()
        job = check_events.delay()
        return JsonResponse(data)

    def get_success_url(self):
        inv_id = self.kwargs['inv_id']
        return reverse('inventory:ajax_inventory_detail', args=(inv_id, ))


# Handles deletion of Part Bulk Upload Files
class PartBulkUploadEventDelete(LoginRequiredMixin, AjaxFormMixin, DeleteView):
    model = BulkUploadEvent
    context_object_name='event_template'
    template_name = 'ooi_ci_tools/part_bulkupload_delete.html'
    redirect_field_name = 'home'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['part_id'] = self.kwargs['part_id']
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {
            'message': "Successfully submitted form data.",
            'object_type': 'bulk_upload_event',
        }
        self.object.delete()
        job = check_events.delay()
        return JsonResponse(data)

    def get_success_url(self):
        part_id = self.kwargs['part_id']
        return reverse('parts:ajax_parts_detail', args=(part_id, ))