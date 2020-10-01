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
import json
import re
import requests
from dateutil import parser
import datetime
from types import SimpleNamespace
from decimal import Decimal

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


from .forms import ImportDeploymentsForm, ImportVesselsForm
from .models import *
from roundabout.userdefinedfields.models import FieldValue, Field
from roundabout.inventory.models import Inventory, Action
from roundabout.parts.models import Part, Revision, Documentation, PartType
from roundabout.assemblies.models import AssemblyType, Assembly, AssemblyPart, AssemblyRevision
from roundabout.inventory.utils import _create_action_history
from roundabout.calibrations.models import CoefficientName, CoefficientValueSet, CalibrationEvent
from roundabout.calibrations.forms import validate_coeff_vals, parse_valid_coeff_vals
from roundabout.users.models import User
from roundabout.cruises.models import Cruise, Vessel


# Github CSV file importer for Vessels
class ImportVesselsUploadView(LoginRequiredMixin, FormView):
    form_class = ImportVesselsForm
    template_name = 'ooi_ci_tools/import_vessels_upload_form.html'

    def form_valid(self, form):
        csv_file = self.request.FILES['vessels_csv']
        # Set up the Django file object for CSV DictReader
        csv_file.seek(0)
        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
        # Get the column headers to save with parent TempImport object
        headers = reader.fieldnames
        # Set up data lists for returning results
        vessels_created = []
        vessels_updated = []

        for row in reader:
            vessel_name = row['Vessel Name']
            print(vessel_name)
            MMSI_number = None
            IMO_number = None
            length = None
            max_speed = None
            max_draft = None
            active = re.sub(r'[()]', '', row['Active'])
            R2R = row['R2R']

            if row['MMSI#']:
                MMSI_number = int(re.sub('[^0-9]','', row['MMSI#']))
                #MMSI_number = int(row['MMSI#'])

            if row['IMO#']:
                IMO_number = int(row['IMO#'])

            if row['Length (m)']:
                length = Decimal(row['Length (m)'])

            if row['Max Speed (m/s)']:
                max_speed = Decimal(row['Max Draft (m)'])

            if row['Max Draft (m)']:
                max_draft = Decimal(row['Max Draft (m)'])

            if active:
                if active == 'Y':
                    active = True
                else:
                    active = False
            if R2R:
                if R2R == 'Y':
                    R2R = True
                else:
                    R2R = False

            # update or create Vessel object based on vessel_name field
            vessel_obj, created = Vessel.objects.update_or_create(
                vessel_name = vessel_name,
                defaults = {
                    'prefix': row['Prefix'],
                    'vessel_designation': row['Vessel Designation'],
                    'ICES_code': row['ICES Code'],
                    'operator': row['Operator'],
                    'call_sign': row['Call Sign'],
                    'MMSI_number': MMSI_number,
                    'IMO_number': IMO_number,
                    'length': length,
                    'max_speed': max_speed,
                    'max_draft': max_draft,
                    'designation': row['Designation'],
                    'active': active,
                    'R2R': R2R,
                },
            )

            if created:
                vessels_created.append(vessel_obj)
            else:
                vessels_updated.append(vessel_obj)

            print(vessels_created)
            print(vessels_updated)

        return super(ImportVesselsUploadView, self).form_valid(form)

    def get_success_url(self):
        return reverse('ooi_ci_tools:import_upload_success', )


# Github CSV file importer for Deployments
# Ths will create a new Asembly Revision and Build for each Deployment
class ImportDeploymentsUploadView(LoginRequiredMixin, FormView):
    form_class = ImportDeploymentsForm
    template_name = 'ooi_ci_tools/import_deployments_upload_form.html'

    def form_valid(self, form):
        csv_files = self.request.FILES.getlist('deployments_csv')
        # Set up the Django file object for CSV DictReader
        for csv_file in csv_files:
            print(csv_file)
            csv_file.seek(0)
            reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
            headers = reader.fieldnames
            deployments = []
            for row in reader:
                if row['mooring.uid'] not in deployments:
                    # get Assembly number from RefDes as that seems to be most consistent across CSVs
                    ref_des = row['Reference Designator']
                    assembly = ref_des.split('-')[0]
                    # build data dict
                    mooring_uid_dict = {'mooring.uid': row['mooring.uid'], 'assembly': assembly, 'rows': []}
                    deployments.append(mooring_uid_dict)

                deployment = next((deployment for deployment in deployments if deployment['mooring.uid']== row['mooring.uid']), False)
                for key, value in row.items():
                    deployment['rows'].append({key: value})

            print(deployments[0])
            for row in deployments[0]['rows']:
                print(row)

        return super(ImportDeploymentsUploadView, self).form_valid(form)

    def get_success_url(self):
        return reverse('ooi_ci_tools:import_upload_success', )


class ImportUploadSuccessView(TemplateView):
    template_name = "ooi_ci_tools/import_upload_success.html"
