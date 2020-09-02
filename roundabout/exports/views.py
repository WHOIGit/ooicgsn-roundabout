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
# built-in Imports
import csv as CSV
import zipfile, io
from os.path import splitext, join
import datetime as dt
from itertools import chain
import warnings

# Django Imports
from django.views.generic import TemplateView, DetailView, ListView
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, OuterRef, Exists, QuerySet, Subquery

# Roundabout Imports
from roundabout.calibrations.models import CalibrationEvent, CoefficientValueSet
from roundabout.configs_constants.models import ConfigEvent, ConfigValue
from roundabout.cruises.models import Cruise, Vessel
from roundabout.inventory.models import Deployment


class HomeView(TemplateView):
    template_name = 'exports/home.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add stuff
        return context


## Single Event Exports ##

class ExportCalibrationEvent(DetailView,LoginRequiredMixin):
    model = CalibrationEvent
    context_object_name = 'cal_event'

    def render_to_response(self, context, **response_kwargs):
        #TODO gotta fetch any ConfigEvents with "export-with-calibrations" rollup flag
        # AHEAD of this calibration but BEFORE next calibration an include ConfigValues from those in csv
        cal = context.get(self.context_object_name)  # getting object from context
        fname = '{}__{}.csv'.format(cal.inventory.serial_number, cal.calibration_date.strftime('%Y%m%d'))

        # Reference to bulk export class
        rows,aux_files = ExportCalibrationEvents.get_csvrows_aux(cal)
        header = ['serial','name','value','notes']
        rows.insert(0,header)

        if aux_files:
            response = HttpResponse(content_type='application/zip')
            fname_zip = '{}.zip'.format(splitext(fname)[0])
            response['Content-Disposition'] = 'inline; filename="{}"'.format(fname_zip)
            zf = zipfile.ZipFile(response, 'w')
            csv_content = io.StringIO()
            writer = CSV.writer(csv_content)
            writer.writerows(rows)
            zf.writestr(fname,csv_content.getvalue())
            for extra_fname,extra_content in aux_files:
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

        # Reference to other bulk export class
        rows = ExportConfigEvents.get_csvrows(confconst)
        header = ['serial','name','value','notes']
        rows.insert(0,header)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'inline; filename="{}"'.format(fname)
        writer = CSV.writer(response)
        writer.writerows(rows)
        return response


## Bulk Export Base Classes ##

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

    @classmethod
    def build_csv(cls, csv, objs):
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

    @classmethod
    def build_zip(cls, zf, objs):
        pass

    @staticmethod
    def zf_safewrite(zf, fname, content):
        """Catch duplicate filenames in zip and rename them with a counter: eg: "fname (1).ext" """
        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            try: zf.writestr(fname, content)
            except UserWarning:
                base, ext = splitext(fname)
                dupes = [zi for zi in zf.infolist() if zi.filename.startswith(base) and zi.filename.endswith(ext)]
                dupe_fname = '{} ({}){}'.format(base, len(dupes), ext)
                zf.writestr(dupe_fname, content)


## Bulk Export Classes ##

# Calibrations Only
class ExportCalibrationEvents(ZipExport):
    model = CalibrationEvent
    fname = 'CalibrationEvents.zip'

    @classmethod
    def build_zip(cls, zf, objs, subdir=None):
        objs = objs.prefetch_related('inventory', 'inventory__fieldvalues', 'inventory__fieldvalues__field')
        for cal in objs:
            csv_fname = '{}__{}.csv'.format(cal.inventory.serial_number, cal.calibration_date.strftime('%Y%m%d'))
            if subdir: csv_fname = join(subdir, csv_fname)

            header = ['serial', 'name', 'value', 'notes']
            rows, aux_files = cls.get_csvrows_aux(cal)
            rows.insert(0, header)

            csv_content = io.StringIO()
            writer = CSV.writer(csv_content)
            writer.writerows(rows)
            cls.zf_safewrite(zf, csv_fname, csv_content.getvalue())
            for extra_fname, extra_content in aux_files:
                cls.zf_safewrite(zf, extra_fname, extra_content)

    @staticmethod
    def get_csvrows_aux(cal):
        serial_label_qs = cal.inventory.fieldvalues.filter(field__field_name__iexact='Manufacturer Serial Number',
                                                           is_current=True)
        if serial_label_qs.exists():
            serial_label = serial_label_qs[0].field_value
        else:
            serial_label = ''

        aux_files = []
        rows = []
        for coeff in cal.coefficient_value_sets.all():
            if coeff.coefficient_name.value_set_type == '2d':
                sn,t,cn = cal.inventory.serial_number, cal.calibration_date.strftime('%Y%m%d'), coeff.coefficient_name
                extra_fname = '{}__{}__{}.ext'.format(sn,t,cn)
                extra = (extra_fname,coeff.value_set)
                aux_files.append(extra)

            row = [serial_label,
                   coeff.coefficient_name.calibration_name,
                   coeff.value_set_with_export_formatting(),
                   coeff.notes]
            rows.append(row)

        return rows, aux_files


# Configs Only
class ExportConfigEvents(ZipExport):
    model = ConfigEvent
    fname = 'ConfigEvents.zip'

    @classmethod
    def build_zip(cls, zf, objs, subdir=None):
        objs = objs.prefetch_related('inventory', 'inventory__fieldvalues', 'inventory__fieldvalues__field')
        for confconst in objs:
            csv_fname = '{}__{}.csv'.format(confconst.inventory.serial_number,
                                            confconst.configuration_date.strftime('%Y%m%d'))
            if subdir: csv_fname = join(subdir, csv_fname)

            header = ['serial', 'name', 'value', 'notes']
            rows = cls.get_csvrows(confconst)
            rows.insert(0, header)

            csv_content = io.StringIO()
            writer = CSV.writer(csv_content)
            writer.writerows(rows)
            cls.zf_safewrite(zf, csv_fname, csv_content.getvalue())

    @staticmethod
    def get_csvrows(confconst, export_with_calibs_only=False):
        filter_kwargs = dict(field__field_name__iexact='Manufacturer Serial Number', is_current=True)
        serial_label_qs = confconst.inventory.fieldvalues.filter(**filter_kwargs)
        if serial_label_qs.exists():
            serial_label = serial_label_qs[0].field_value
        else:
            serial_label = ''

        rows = []
        for confconst_val in confconst.config_values.all():
            if export_with_calibs_only and not confconst_val.config_name.include_with_calibrations: continue
            row = [serial_label,
                   confconst_val.config_name.name,
                   confconst_val.config_value_with_export_formatting(),
                   confconst_val.notes]
            rows.append(row)

        return rows


# Calibrations WITH Configs
class ExportCalibrationEvents_withConfigs(ZipExport):
    model = None
    fname = 'CalibrationEvents_withConfigs.zip'

    @classmethod
    def get_queryset(cls):

        # most recent first
        calib_qs = CalibrationEvent.objects.all().annotate(date = F('calibration_date')).order_by('-date')
        config_qs = ConfigEvent.objects.all().annotate(date = F('configuration_date')).order_by('-date')

        # keep configs where at least one ConfigValue has include_with_calibration=True
        include_with_calibs = ConfigValue.objects.filter(config_event=OuterRef('pk'), config_name__include_with_calibrations=True)
        config_qs = config_qs.annotate(include=Exists(include_with_calibs)).filter(include=True)

        # merging is not allowed on different models.
        # instead, lets pre-bundle these by instrument
        instrument_IDs = set(calib_qs.values_list('inventory__id',flat=True)).union(config_qs.values_list('inventory__id',flat=True))
        qs = dict()
        for inst_id in instrument_IDs:
            inst_calib_qs = calib_qs.filter(inventory__id=inst_id)
            inst_config_qs = config_qs.filter(inventory__id=inst_id)
            if inst_calib_qs.exists() and inst_config_qs.exists():
                inst_qs = chain(inst_calib_qs,inst_config_qs)
            elif inst_calib_qs.exists():
                inst_qs = inst_calib_qs
            else: # inst_config_qs.exists()
                inst_qs = inst_config_qs
            qs[inst_id] = inst_qs
        return qs

    @classmethod
    def build_zip(cls, zf, objs, subdir=None):
        # objs here is a dict, not a real queryset.
        # Each key is an inst_id,
        # and each val is either (a) a queryset of CalibEvents,
        #                        (b) a queryset of ConfigEvent, or
        #                        (c) a list of CalibEvents and ConfigEvents
        # for (c), vals are paired or "bundled" in a tuple bearing calib and/or config events
        # (a) and (b) follow the same schema (as singlets)
        for inv_objs in objs.values():
            if isinstance(inv_objs,QuerySet):
                # one csv per object, all obj will be of same model.
                for obj in inv_objs:
                    bundle = (obj,None)
                    cls.write_csv(zf, bundle, subdir)

            else: # theres a mix of CalibrationEvents and ConfigEvents.
                # calibs carry forwards with each new config until the next calib.
                # consts always carry forward.
                # consecutive and trailing calibs need-not be bundled.
                inv_objs =  sorted(inv_objs,key=lambda x: x.date ) # earliest first

                # TESTING #
                #if inv_objs[0].inventory.serial_number == 'CGINS-CTDBPF-50001':
                #    obj_type = [obj.config_values.all()[0].config_name.config_type if isinstance(obj,ConfigEvent) else 'CALIB' for obj in inv_objs]
                #    dates = [obj.date.strftime('%Y-%m-%d') for obj in inv_objs]
                #    TBDs = [obj.deployment.current_status if obj.deployment else 'NA' for obj in inv_objs]
                #    x = list(zip(inv_objs,obj_type, dates, TBDs))
                #    print(x)

                bundled_objs = []
                prev, calib, config, const = None, None, None, None
                for obj in inv_objs:
                    if isinstance(obj,CalibrationEvent):
                        calib=obj
                    elif isinstance(obj,ConfigEvent):
                        if all([cv.config_name.config_type=='cnst' for cv in obj.config_values.all()]):
                            const=obj
                        else: # it's a config.
                            if obj.deployment: # ie not "TBD"
                                config=obj
                            else: continue # skip it if it's TBD, ie not "deployed".

                    if obj==config:
                        # config obj's always result in a new csv, incl. previous calibration if any
                        bundled_objs.append( (calib,config,const) )
                    elif obj==calib and isinstance(prev,CalibrationEvent):
                        # consecutive calibrations get their own csv's
                        bundled_objs.append( (prev,None,const) )

                    if obj!=const:
                        prev = obj  # note previous object, unless it's a constant

                # make sure not to skip an end-of-loop trailing Calibration
                if isinstance(prev,CalibrationEvent):
                    bundled_objs.append( (prev,None,const) )

                # write bundles to zip as csv's
                for bundle in bundled_objs:
                    cls.write_csv(zf, bundle, subdir)


    @classmethod
    def write_csv(cls, zf, bundle, subdir=None):
        fname_obj = bundle[1] or bundle[0] # config is in bundle[1] if avail
        csv_fname = '{}__{}.csv'.format(fname_obj.inventory.serial_number, fname_obj.date.strftime('%Y%m%d'))
        csv_content = io.StringIO()
        csv_writer = CSV.writer(csv_content)
        header = ['serial', 'name', 'value', 'notes']
        has_content = None
        csv_writer.writerow(header)

        approvals = [obj.approved for obj in bundle if obj is not None]
        #if not all(approvals): return  # TODO

        for obj in bundle:
            if isinstance(obj,CalibrationEvent):
                # Reference to Calibrations-Only Class
                rows, aux_files = ExportCalibrationEvents.get_csvrows_aux(obj)
                if rows: has_content = True
                csv_writer.writerows(rows)
                for extra_fname, extra_content in aux_files:
                    if subdir: extra_fname = join(subdir, extra_fname)
                    cls.zf_safewrite(zf, extra_fname, extra_content)

            elif isinstance(obj,ConfigEvent):
                # Reference to Configs-Only Class
                rows = ExportConfigEvents.get_csvrows(obj,export_with_calibs_only=True)
                if rows: has_content = True
                csv_writer.writerows(rows)

        # write csv to zip
        if subdir: csv_fname = join(subdir, csv_fname)
        if has_content: # avoid blank files
            cls.zf_safewrite(zf, csv_fname, csv_content.getvalue())


# Cruises CSV
class ExportCruises(CSVExport):
    model = Cruise
    fname = 'CruiseInformation.csv'
    ordering = ['cruise_start_date']
    #see https://github.com/oceanobservatories/asset-management/tree/master/cruise

    @classmethod
    def build_csv(cls, csv, objs):
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


# Vessels CSV
class ExportVessels(CSVExport):
    model = Vessel
    fname = 'shiplist.csv'
    ordering = ['prefix']
    # see https://github.com/oceanobservatories/asset-management/tree/master/vessel

    @classmethod
    def build_csv(cls, csv, objs):
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


# Deployment Bulk Export
class ExportDeployments(ZipExport):
    model = Deployment
    fname = 'Deployments.zip'

    @classmethod
    def build_zip(cls, zf, objs, subdir=None):
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
            cls.zf_safewrite(zf, csv_fname, csv_content.getvalue())


# Bulk Export Combo!!
class ExportCI(ZipExport):
    model=None
    fname='asset-management.zip'
    def get_queryset(self):
        return None

    @classmethod
    def build_zip(cls, zf, objs):

        # Deployment csv's
        deployments = Deployment.objects.all()
        ExportDeployments.build_zip(      zf, deployments,  subdir='deployment')

        # Calibration csv's
        ccc = ExportCalibrationEvents_withConfigs.get_queryset()
        ExportCalibrationEvents_withConfigs.build_zip(zf, ccc, subdir='calibration')

        # Cruises csv
        cruises = Cruise.objects.all()
        cruise_csv_fname = join('cruise',ExportCruises.fname)
        cruise_csv_content = io.StringIO()
        cruise_csv = CSV.writer(cruise_csv_content)
        ExportCruises.build_csv(  cruise_csv, cruises)
        zf.writestr(cruise_csv_fname,cruise_csv_content.getvalue())

        # Vessels csv
        vessels = Vessel.objects.all()
        vessel_csv_fname = join('vessel',ExportVessels.fname)
        vessel_csv_content = io.StringIO()
        vessel_csv = CSV.writer(vessel_csv_content)
        ExportVessels.build_csv(  vessel_csv, vessels)
        zf.writestr(vessel_csv_fname,vessel_csv_content.getvalue())
