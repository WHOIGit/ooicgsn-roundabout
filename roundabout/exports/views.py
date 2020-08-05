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
import csv as CSV
import zipfile, io
from os.path import splitext, join
import datetime as dt

from django.views.generic import TemplateView, DetailView, ListView
from django.http import HttpResponse,HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin

from roundabout.calibrations.models import CalibrationEvent
from roundabout.configs_constants.models import ConfigEvent
from roundabout.cruises.models import Cruise, Vessel
from roundabout.inventory.models import Deployment


class HomeView(TemplateView):
    template_name = 'exports/home.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add stuff
        return context


class ExportCalibrationEvent(DetailView,LoginRequiredMixin):
    model = CalibrationEvent
    context_object_name = 'cal_event'

    def render_to_response(self, context, **response_kwargs):
        #TODO gotta fetch any ConfigEvents with "export-with-calibrations" rollup flag
        # AHEAD of this calibration but BEFORE next calibration an include ConfigValues from those in csv
        cal = context.get(self.context_object_name)  # getting object from context
        fname = '{}__{}.csv'.format(cal.inventory.serial_number, cal.calibration_date.strftime('%Y%m%d'))

        serial_label_qs = cal.inventory.fieldvalues.filter(field__field_name__iexact='Manufacturer Serial Number', is_current=True)
        if serial_label_qs.exists():
            serial_label = serial_label_qs[0].field_value
        else:
            serial_label = '' #cal.inventory.old_serial_number or cal.inventory.serial_number

        zip_mode = []
        header = ['serial','name','value','notes']
        rows = [header]
        for coeff in cal.coefficient_value_sets.all():
            if coeff.coefficient_name.value_set_type == '2d':
                extra = ('{}__{}.ext'.format(splitext(fname)[0], coeff.coefficient_name),
                         coeff.value_set)
                zip_mode.append(extra)

            row = [serial_label,
                   coeff.coefficient_name.calibration_name,
                   coeff.value_set_with_export_formatting(),
                   coeff.notes]
            rows.append(row)

        if zip_mode:
            response = HttpResponse(content_type='application/zip')
            fname_zip = '{}.zip'.format(splitext(fname)[0])
            response['Content-Disposition'] = 'inline; filename="{}"'.format(fname_zip)
            zf = zipfile.ZipFile(response, 'w')
            csv_content = io.StringIO()
            writer = CSV.writer(csv_content)
            writer.writerows(rows)
            zf.writestr(fname,csv_content.getvalue())
            for extra_fname,extra_content in zip_mode:
                zf.writestr(extra_fname, extra_content)
            return response

        else:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'inline; filename="{}"'.format(fname)
            writer = CSV.writer(response)
            writer.writerows(rows)
            return response

class ExportConfigEvent(DetailView,LoginRequiredMixin):
    model = ConfigEvent
    context_object_name = 'confconst'

    def render_to_response(self, context, **response_kwargs):
        confconst = context.get(self.context_object_name)  # getting object from context
        fname = '{}__{}.csv'.format(confconst.inventory.serial_number, confconst.configuration_date.strftime('%Y%m%d'))

        serial_label_qs = confconst.inventory.fieldvalues.filter(field__field_name__iexact='Manufacturer Serial Number', is_current=True)
        if serial_label_qs.exists():
            serial_label = serial_label_qs[0].field_value
        else:
            serial_label = ''

        header = ['serial','name','value','notes']
        rows = [header]
        for confconst_val in confconst.config_values.all():
            row = [serial_label,
                   confconst_val.config_name.name,
                   confconst_val.config_value_with_export_formatting(),
                   confconst_val.notes]
            rows.append(row)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'inline; filename="{}"'.format(fname)
        writer = CSV.writer(response)
        writer.writerows(rows)
        return response


class CSVExport(ListView,LoginRequiredMixin):
    model = None
    fname = '{}.csv'
    context_object_name = 'objs'
    def render_to_response(self, context, **response_kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'inline; filename="{}"'.format(self.fname)
        csv_writer = CSV.writer(response)
        objs = context.get(self.context_object_name)
        self.build_csv(csv_writer, objs)
        return response

    @staticmethod
    def build_csv(csv, objs):
        pass


class ZipExport(ListView,LoginRequiredMixin):
    model = None
    fname = '{}.zip'
    context_object_name = 'objs'
    def render_to_response(self, context, **response_kwargs):
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = 'inline; filename="{}"'.format(self.fname)
        objs = context.get(self.context_object_name)
        zf = zipfile.ZipFile(response, 'w')
        self.build_zip(zf, objs)
        return response

    @staticmethod
    def build_zip(zf, objs):
        pass


class ExportCalibrationEvents(ZipExport):
    model = CalibrationEvent
    fname = 'CalibrationEvents.zip'

    def get_queryset(self):
        qs = super(ZipExport, self).get_queryset()

        return qs

    @staticmethod
    def build_zip(zf, objs, subdir=None):
        objs = objs.prefetch_related('inventory','inventory__fieldvalues','inventory__fieldvalues__field')
        for cal in objs:
            csv_fname = '{}__{}.csv'.format(cal.inventory.serial_number, cal.calibration_date.strftime('%Y%m%d'))
            if subdir: csv_fname = join(subdir,csv_fname)

            serial_label_qs = cal.inventory.fieldvalues.filter(field__field_name__iexact='Manufacturer Serial Number', is_current=True)
            if serial_label_qs.exists():
                serial_label = serial_label_qs[0].field_value
            else:
                serial_label = ''

            aux_files = []
            header = ['serial', 'name', 'value', 'notes']
            rows = [header]
            for coeff in cal.coefficient_value_sets.all():
                if coeff.coefficient_name.value_set_type == '2d':
                    extra = ('{}__{}.ext'.format(splitext(csv_fname)[0], coeff.coefficient_name),
                             coeff.value_set)
                    aux_files.append(extra)

                row = [serial_label,
                       coeff.coefficient_name.calibration_name,
                       coeff.value_set_with_export_formatting(),
                       coeff.notes]
                rows.append(row)

            csv_content = io.StringIO()
            writer = CSV.writer(csv_content)
            writer.writerows(rows)
            zf.writestr(csv_fname, csv_content.getvalue())
            for extra_fname, extra_content in aux_files:
                zf.writestr(extra_fname, extra_content)
        # todo include config/const objects with an "export with configurations" flag True


class ExportConfigEvents(ZipExport):
    model = ConfigEvent
    fname = 'ConfigEvents.zip'

    @staticmethod
    def build_zip(zf, objs, subdir=None):
        objs = objs.prefetch_related('inventory','inventory__fieldvalues','inventory__fieldvalues__field')
        for confconst in objs:
            csv_fname = '{}__{}.csv'.format(confconst.inventory.serial_number, confconst.configuration_date.strftime('%Y%m%d'))
            if subdir: csv_fname = join(subdir,csv_fname)

            serial_label_qs = confconst.inventory.fieldvalues.filter(field__field_name__iexact='Manufacturer Serial Number', is_current=True)
            if serial_label_qs.exists():
                serial_label = serial_label_qs[0].field_value
            else:
                serial_label = ''

            header = ['serial', 'name', 'value', 'notes']
            rows = [header]
            for confconst_val in confconst.config_values.all():
                row = [serial_label,
                       confconst_val.config_name.name,
                       confconst_val.config_value_with_export_formatting(),
                       confconst_val.notes]
                rows.append(row)

            csv_content = io.StringIO()
            writer = CSV.writer(csv_content)
            writer.writerows(rows)
            zf.writestr(csv_fname, csv_content.getvalue())


class ExportCruises(CSVExport):
    model = Cruise
    fname = 'CruiseInformation.csv'
    ordering = ['cruise_start_date']
    #see https://github.com/oceanobservatories/asset-management/tree/master/cruise

    @staticmethod
    def build_csv(csv, objs):
        objs = objs.prefetch_related('vessel')
        header_att = [('CUID',                  'CUID'),
                      ('ShipName',              'friendly_name'),
                      ('cruiseStartDateTime',   'cruise_start_date'),
                      ('cruiseStopDateTime',    'cruise_stop_date'),
                      ('notes',                 'notes'),
                      ]
        headers, attribs = zip(*header_att)
        csv.writerow(headers)
        for cruise in objs:
            row = list()
            row.append(cruise.CUID)
            row.append(getattr(cruise.vessel,'vessel_name',''))
            row.append(cruise.cruise_start_date.replace(tzinfo=None).isoformat())
            row.append(cruise.cruise_stop_date.replace(tzinfo=None).isoformat())
            #location = cruise.location or ''
            notes = cruise.notes or ''
            row.append(row.append(notes))
            csv.writerow(row)


class ExportVessels(CSVExport):
    model = Vessel
    fname = 'shiplist.csv'
    ordering = ['prefix']
    # see https://github.com/oceanobservatories/asset-management/tree/master/vessel

    @staticmethod
    def build_csv(csv, objs):
        header_att = [('Prefix',                'prefix'),
                      ('Vessel Designation',    'vessel_designation'),
                      ('Vessel Name',           'vessel_name'),
                      ('ICES Code',             'ICES_code'),
                      ('Operator',              'operator'),
                      ('Call Sign',             'call_sign'),
                      ('MMSI#',                 'MMSI_number'),
                      ('IMO#',                  'IMO_number'),
                      ('Length (m)',            'length'),
                      ('Max Speed (m/s)',       'max_speed'),
                      ('Max Draft (m)',         'max_draft'),
                      ('Designation',           'designation'),
                      ('Active',                'active'),
                      ('R2R',                   'R2R'),
                     #('Notes',                 'notes'),
                      ]
        headers,attribs = zip(*header_att)
        csv.writerow(headers)
        for vessel in objs:
            row = []
            for att in attribs:
                val = getattr(vessel,att,None)
                if val is None:
                    val = ''
                elif isinstance(val,bool):
                    val = 'Y' if val else 'N'
                    if att=='active' and val=='N': val = '(N)'
                row.append(str(val))
            csv.writerow(row)


class ExportDeployments(ZipExport): # ZipExportCSV
    model = Deployment
    fname = 'Deployments.zip'

    @staticmethod
    def build_zip(zf, objs, subdir=None):
        header_att = [('CUID_Deploy',           'cruise_deployed'),
                      ('deployedBy',            ''),
                      ('CUID_Recover',          'cruise_recovered'),
                      ('recoveredBy',           ''),
                      ('Reference Designator',  ''),
                      ('deploymentNumber',      'deployment_number'),
                      ('versionNumber',         ''),
                      ('startDateTime',         'deployment_to_field_date'),
                      ('stopDateTime',          'deployment_recovery_date'),
                      ('mooring.uid',           ''),
                      ('node.uid',              ''),
                      ('sensor.uid',            ''),
                      ('lat',                   'latitude'),
                      ('lon',                   'longitude'),
                      ('orbit',                 ''),
                      ('deployment_depth',      'depth'),
                      ('water_depth',           'depth'),
                      ('notes',                 ''), ]
        headers, attribs = zip(*header_att)

        def depl_row(depl_obj, attribs):
            row = []
            for att in attribs:
                val = getattr(depl_obj, att, None)
                if val is None:
                    val = ''  # TODO check udf's
                elif isinstance(val, dt.datetime):  # dates
                    val = val.replace(tzinfo=None)  # remove timezone awareness such that
                    val = val.isoformat(timespec='seconds')  # +00:00 doesn't appear in iso string
                elif isinstance(val, float):  # lat,lon
                    val = '{:.5f}'.format(val)
                row.append(str(val))
            return row

        objs = objs.prefetch_related('build__assembly_revision__assembly')
        assy_names = objs.values_list('build__assembly_revision__assembly__name',flat=True)
        assy_names = set(assy_names)
        #assy_names.discard(None) # removes None if any
        for assy_name in assy_names:
            csv_fname = '{}_Deploy.csv'.format(str(assy_name).replace(' ','_'))
            if subdir: csv_fname = join(subdir,csv_fname)
            csv_content = io.StringIO()
            csv = CSV.writer(csv_content)
            csv.writerow(headers)
            for depl in objs.filter(build__assembly_revision__assembly__name__exact=assy_name):
                row = depl_row(depl,attribs)
                csv.writerow(row)
                #for inv_depl in depl.inventory_deployments.all():
                #    row = self.depl_row(inv_depl,attribs)
                #    csv.writerow(row)
            zf.writestr(csv_fname,csv_content.getvalue())


class ExportCI(ZipExport):
    model=None
    fname='asset-management.zip'
    def get_queryset(self):
        return None

    @staticmethod
    def build_zip(zf, objs):

        deployments = Deployment.objects.all()
        ExportDeployments.build_zip(      zf, deployments,  subdir='deployment')

        calibrations = CalibrationEvent.objects.all()
        ExportCalibrationEvents.build_zip(zf, calibrations, subdir='calibration')

        cruises = Cruise.objects.all()
        cruise_csv_fname = join('cruise',ExportCruises.fname)
        cruise_csv_content = io.StringIO()
        cruise_csv = CSV.writer(cruise_csv_content)
        ExportCruises.build_csv(  cruise_csv, cruises)
        zf.writestr(cruise_csv_fname,cruise_csv_content.getvalue())

        vessels = Vessel.objects.all()
        vessel_csv_fname = join('vessel',ExportVessels.fname)
        vessel_csv_content = io.StringIO()
        vessel_csv = CSV.writer(vessel_csv_content)
        ExportVessels.build_csv(  vessel_csv, vessels)
        zf.writestr(vessel_csv_fname,vessel_csv_content.getvalue())
