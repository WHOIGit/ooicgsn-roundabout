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

import json
import socket
import os
import xml.etree.ElementTree as ET
import csv

from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, QueryDict
from django.db.models import Q
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from itertools import chain

from roundabout.assemblies.models import Assembly
from roundabout.inventory.models import Inventory
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision
from roundabout.admintools.models import Printer
from roundabout.assemblies.models import AssemblyPart
from roundabout.builds.models import Build, BuildAction
from roundabout.userdefinedfields.models import Field



class ReportsHome(LoginRequiredMixin, TemplateView):
    template_name = 'reports/reports_home.html'

    def get_context_data(self, **kwargs):
        context = super(ReportsHome, self).get_context_data(**kwargs)

        context.update({'node_type':     'inventory',
                        'navtree_title': 'Inventory',
                        'navtree_url':   reverse('inventory:ajax_load_inventory_navtree')})

        return context

class BuildReport(LoginRequiredMixin, DetailView):
    model = Build
    context_object_name = 'build'
    template_name = 'reports/build_report.html'

    def get_context_data(self, **kwargs):
        context = super(BuildReport, self).get_context_data(**kwargs)
        sections=['GPS','FBB','ISU','SBD','FREEWAVE','WIFI','XEOS','FLASHER']
        for query in [s.lower() for s in sections]:
            context[query+'_inv'] = context['build'].inventory.filter(part__name__icontains=query)
        return context

class BuildReportCsvDownload(LoginRequiredMixin, View):

    def get(self,request, pk):
        build = Build.objects.prefetch_related('inventory__part').get(id=pk)
        fields = Field.objects.all().order_by('id')

        response = HttpResponse(content_type='text/csv')
        filename = "{}.{}.report.csv".format(build.name.replace(' ','_'), build.build_number.replace(' ','_'))
        response['Content-Disposition'] = 'attachment; filename='+filename

        header = ['Type','SN','Name']
        udf_headers = ['UDF:'+f.field_name for f in fields]
        header = header + udf_headers
        sections=['GPS','FBB','ISU','SBD','FREEWAVE','WIFI','XEOS','FLASHER']
        rows=[]

        for query in sections:
            invs = build.inventory.filter(part__name__icontains=query)
            for inv in invs: # if any
                #collect user defined field values of inventory item by field id
                udf_vals = {udf.field.id:udf.field_value for udf in inv.part.fieldvalues.all()}
                udf_row = []
                #if it exists, add it to the list, otherwise leave a blank
                for field in fields:
                    try: udf_row.append(udf_vals[field.id])
                    except KeyError as e:
                        udf_row.append('')
                row = [query,inv.serial_number,inv.part.name] + udf_row
                rows.append(row)

        writer = csv.writer(response)
        writer.writerow(header)
        writer.writerows(rows)

        return response
