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
import datetime as dt
import io
import warnings
import zipfile
from os.path import splitext, join
from sys import stdout
from operator import attrgetter
from unicodedata import normalize


# Django Imports
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, OuterRef, Exists
from django.http import HttpResponse
from django.views.generic import TemplateView, DetailView, ListView

# Roundabout Imports
from roundabout.calibrations.models import CalibrationEvent
from roundabout.configs_constants.models import ConfigEvent, ConfigValue, ConfigName
from roundabout.cruises.models import Cruise, Vessel
from roundabout.inventory.models import Inventory, Deployment, InventoryDeployment
from roundabout.ooi_ci_tools.models import ReferenceDesignator, ReferenceDesignatorEvent
from roundabout.userdefinedfields.models import FieldValue
from roundabout.assemblies.models import Assembly


class HomeView(TemplateView):
    template_name = "exports/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add stuff
        return context


## Single Event Exports ##


class ExportCalibrationEvent(DetailView, LoginRequiredMixin):
    model = CalibrationEvent
    context_object_name = "cal_event"

    def render_to_response(self, context, **response_kwargs):
        cal = context.get(self.context_object_name)  # getting object from context
        fname = "{}__{}.csv".format(
            cal.inventory.serial_number, cal.calibration_date.strftime("%Y%m%d")
        )

        # Reference to bulk export class
        rows, aux_files = ExportCalibrationEvents.get_csvrows_aux(cal)
        header = ["serial", "name", "value", "notes"]
        rows.insert(0, header)

        if aux_files:
            response = HttpResponse(content_type="application/zip")
            fname_zip = "{}.zip".format(splitext(fname)[0])
            response["Content-Disposition"] = 'inline; filename="{}"'.format(fname_zip)
            zf = zipfile.ZipFile(response, "w")
            csv_content = io.StringIO()
            writer = CSV.writer(csv_content)
            writer.writerows(rows)
            zf.writestr(fname, csv_content.getvalue())
            for extra_fname, extra_content in aux_files:
                zf.writestr(extra_fname, extra_content)
            return response

        else:
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'inline; filename="{}"'.format(fname)
            writer = CSV.writer(response)
            writer.writerows(rows)
            return response


class ExportConfigEvent(DetailView, LoginRequiredMixin):
    model = ConfigEvent
    context_object_name = "confconst"

    def render_to_response(self, context, **response_kwargs):
        confconst = context.get(self.context_object_name)  # getting object from context
        fname = "{}__{}.csv".format(
            confconst.inventory.serial_number,
            confconst.configuration_date.strftime("%Y%m%d"),
        )

        # Reference to other bulk export class
        rows = ExportConfigEvents.get_csvrows(confconst)
        header = ["serial", "name", "value", "notes"]
        rows.insert(0, header)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'inline; filename="{}"'.format(fname)
        writer = CSV.writer(response)
        writer.writerows(rows)
        return response


## Bulk Export Base Classes ##


class CSVExport(ListView, LoginRequiredMixin):
    model = None
    fname = "{}.csv"
    context_object_name = "objs"

    def render_to_response(self, context, **response_kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'inline; filename="{}"'.format(self.fname)
        csv_writer = CSV.writer(response)
        objs = context.get(self.context_object_name)
        CI_mode = "ci" in self.request.GET
        self.build_csv(csv_writer, objs, CI_mode)
        return response

    @classmethod
    def build_csv(cls, csv, objs, CI_mode=False):
        pass


class ZipExport(ListView, LoginRequiredMixin):
    model = None
    fname = "{}.zip"
    context_object_name = "objs"

    def render_to_response(self, context, **response_kwargs):
        response = HttpResponse(content_type="application/zip")
        response["Content-Disposition"] = 'inline; filename="{}"'.format(self.fname)
        objs = context.get(self.context_object_name)
        zf = zipfile.ZipFile(response, "w")
        self.build_zip(zf, objs)
        return response

    @classmethod
    def build_zip(cls, zf, objs):
        pass

    @staticmethod
    def zf_safewrite(zf, fname, content, mode=("count", "skip", None)[0]):
        """
        Catch duplicate filename to be written into zip and respond according to "mode".
            mode=count: rename duplicate filename to include a counter: eg: "fname (1).ext"
            mode=skip: incoming duplicate filename is not written to the zip
            mode=None: duplicate filename is written into zip anyways (the default zf.writestr() behavior)
        Default mode is "count".
        """
        if mode:
            with warnings.catch_warnings():
                warnings.filterwarnings("error")
                try:
                    zf.writestr(fname, content)
                except UserWarning:
                    if mode == "count":
                        base, ext = splitext(fname)
                        dupes = [
                            zi
                            for zi in zf.infolist()
                            if zi.filename.startswith(base)
                            and zi.filename.endswith(ext)
                        ]
                        dupe_fname = "{} ({}){}".format(base, len(dupes), ext)
                        zf.writestr(dupe_fname, content)
                    else:  # mode=='skip'
                        pass  # file is not written

        else:  # regular zf filewrite. zip may include duplicate filenames
            zf.writestr(fname, content)


## Bulk Export Classes ##


# Calibrations Only
class ExportCalibrationEvents(ZipExport):
    model = CalibrationEvent
    fname = "CalibrationEvents.zip"

    @classmethod
    def build_zip(cls, zf, objs, subdir=None):
        objs = objs.select_related("inventory__part__part_type").exclude(
            inventory__part__part_type__ccc_toggle=False
        )
        objs = objs.select_related("inventory__location").exclude(
            inventory__location__root_type="Trash"
        )
        objs = objs.prefetch_related(
            "inventory", "inventory__fieldvalues", "inventory__fieldvalues__field"
        )

        for cal in objs:
            csv_fname = "{}__{}.csv".format(
                cal.inventory.serial_number, cal.calibration_date.strftime("%Y%m%d")
            )
            if subdir:
                csv_fname = join(subdir, csv_fname)

            header = ["serial", "name", "value", "notes"]
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
        serial_label_qs = cal.inventory.fieldvalues.filter(
            field__field_name__iexact="Manufacturer Serial Number", is_current=True
        )
        if serial_label_qs.exists():
            serial_label = serial_label_qs[0].field_value
        else:
            serial_label = ""

        # hotfix issue 211
        if "OPTAA" in cal.inventory.part.name:
            serial_label = "ACS-" + serial_label

        aux_files = []
        rows = []
        for coeff in cal.coefficient_value_sets.all():
            if coeff.coefficient_name.value_set_type == "2d":
                sn, t, cn = (
                    cal.inventory.serial_number,
                    cal.calibration_date.strftime("%Y%m%d"),
                    coeff.coefficient_name,
                )
                extra_fname = "{}__{}__{}.ext".format(sn, t, cn)
                extra = (extra_fname, coeff.value_set)
                aux_files.append(extra)

            row = [
                serial_label,
                coeff.coefficient_name.calibration_name,
                coeff.value_set_with_export_formatting(),
                coeff.notes,
            ]
            rows.append(row)

        return rows, aux_files


# Configs Only
class ExportConfigEvents(ZipExport):
    model = ConfigEvent
    fname = "ConfigEvents.zip"

    @classmethod
    def build_zip(cls, zf, objs, subdir=None):
        objs = objs.select_related("inventory__part__part_type").exclude(
            inventory__part__part_type__ccc_toggle=False
        )
        objs = objs.select_related("inventory__location").exclude(
            inventory__location__root_type="Trash"
        )
        objs = objs.prefetch_related(
            "inventory", "inventory__fieldvalues", "inventory__fieldvalues__field"
        )

        for confconst in objs:
            csv_fname = "{}__{}.csv".format(
                confconst.inventory.serial_number,
                confconst.configuration_date.strftime("%Y%m%d"),
            )
            if subdir:
                csv_fname = join(subdir, csv_fname)

            header = ["serial", "name", "value", "notes"]
            rows = cls.get_csvrows(confconst)
            rows.insert(0, header)

            csv_content = io.StringIO()
            writer = CSV.writer(csv_content)
            writer.writerows(rows)
            cls.zf_safewrite(zf, csv_fname, csv_content.getvalue())

    @staticmethod
    def get_csvrows(confconst, export_with_calibs_only=False):
        filter_kwargs = dict(
            field__field_name__iexact="Manufacturer Serial Number", is_current=True
        )
        serial_label_qs = confconst.inventory.fieldvalues.filter(**filter_kwargs)
        if serial_label_qs.exists():
            serial_label = serial_label_qs[0].field_value
        else:
            serial_label = ""

        # hotfix issue 211
        if "OPTAA" in confconst.inventory.part.name:
            serial_label = "ACS-" + serial_label

        rows = []
        for confconst_val in confconst.config_values.all():
            if (
                export_with_calibs_only
                and not confconst_val.config_name.include_with_calibrations
            ):
                continue
            row = [
                serial_label,
                confconst_val.config_name.name,
                confconst_val.config_value_with_export_formatting(),
                confconst_val.notes,
            ]
            rows.append(row)

        return rows


# Calibrations WITH Configs
class ExportCalibrationEvents_withConfigs(ZipExport):
    model = None
    fname = "CalibrationEvents_withConfigs.zip"

    @classmethod
    def get_queryset(cls):
        # most recent first
        calib_qs = (
            CalibrationEvent.objects.all()
            .annotate(date=F("calibration_date"))
            .order_by("-date")
        )
        config_qs = (
            ConfigEvent.objects.all()
            .annotate(date=F("configuration_date"))
            .order_by("-date")
        )

        # keep only CCCs that are active in the part-template
        config_qs = config_qs.select_related("inventory__part__part_type").exclude(
            inventory__part__part_type__ccc_toggle=False
        )
        calib_qs = calib_qs.select_related("inventory__part__part_type").exclude(
            inventory__part__part_type__ccc_toggle=False
        )

        # keep only configs where at least one ConfigValue has include_with_calibration=True
        include_with_calibs = ConfigValue.objects.filter(
            config_event=OuterRef("pk"), config_name__include_with_calibrations=True
        )
        config_qs = config_qs.annotate(include=Exists(include_with_calibs)).filter(
            include=True
        )

        # merging is not allowed on different models.
        # instead, lets pre-bundle these by instrument
        instrument_IDs = set(calib_qs.values_list("inventory__id", flat=True)).union(
            config_qs.values_list("inventory__id", flat=True)
        )
        qs = dict()
        for inst_id in instrument_IDs:
            inst_calib_qs = calib_qs.filter(inventory__id=inst_id)
            inst_config_qs = config_qs.filter(inventory__id=inst_id)
            configs_by_deployment = dict()
            if inst_config_qs.exists():  # group by deployment
                deployment_IDs = set(
                    inst_config_qs.values_list("deployment__id", flat=True)
                )
                for dep_id in deployment_IDs:
                    configs_by_deployment[dep_id] = inst_config_qs.filter(
                        deployment__id=dep_id
                    )
            qs[inst_id] = dict(
                calibs=inst_calib_qs, configs_by_deployment=configs_by_deployment
            )
        return qs

    @classmethod
    def build_zip(
        cls, zf, objs, subdir=None, verbose="CalibrationsWithConfigs_EXPORTLOG.txt"
    ):
        # objs here is a dict-of-dicts, not a queryset.
        # Each top-level key is an inst_id.
        # Per inst_id there is (a) a "calibs" key containing a CalibrationEvent Queryset
        #                      (b) a "configs_by_deployment" key containing a dict.
        #                          Each sub-key here is a deployment_id, the value of which is a ConfigEvent Queryset
        # If all calibs and configs are valid for an inst_id, then they are bundled and sent to write_csv().
        # To be valid, the bundled inventory CCC fields must (1) include all the part's inventory CCC fields
        #                                                    (2) be approved==True

        # if verbose is a string, a log file with that string name is included in the export
        if isinstance(verbose, str):
            if subdir:
                verbose = join(subdir, verbose)
            out = io.StringIO()
        else:
            out = stdout

        for inv_id, inv_objs in objs.items():
            # CCC events
            calibs_qs = inv_objs["calibs"]
            configs_by_deployment = inv_objs["configs_by_deployment"]

            # PART VALUES TO CHECK AGAINST
            the_inv = Inventory.objects.filter(id=inv_id)[0]
            print("\nInv:", the_inv, "(id={})".format(inv_id), file=out)
            print("Inv calibs:", calibs_qs if calibs_qs.exists() else None, file=out)
            print("Inv confconst", configs_by_deployment, file=out)

            if the_inv.location.root_type == "Trash":
                print("FAIL:", the_inv, "is in the Trash. Skip-it.", file=out)
                continue
            elif not the_inv.assembly_part:
                print(
                    "FAIL:",
                    the_inv,
                    "does not have an associated assembly_part!",
                    file=out,
                )
                continue
            the_part = the_inv.assembly_part.part
            calibs_to_match = (
                set(the_part.part_coefficientnameevents.first().coefficient_names.all())
                if the_part.part_coefficientnameevents.first()
                else set()
            )
            calibs_to_match = {field.calibration_name for field in calibs_to_match}
            confconsts_to_match = (
                set(
                    the_part.part_confignameevents.first().config_names.filter(
                        include_with_calibrations=True
                    )
                )
                if the_part.part_confignameevents.first()
                else set()
            )
            confconsts_to_match = {field.name for field in confconsts_to_match}
            print("Part:", the_part, "(id={})".format(the_part.id), file=out)
            print(
                "Part calib fields     (REQUIRED):",
                calibs_to_match if calibs_to_match else "{}",
                file=out,
            )
            print(
                "Part confconst fields (REQUIRED):",
                confconsts_to_match if confconsts_to_match else "{}",
                file=out,
            )

            if calibs_to_match and not confconsts_to_match:
                print('MODE: "part has calibs ONLY"', file=out)
                if not (calibs_qs and not configs_by_deployment):
                    print(
                        "  WARNING: inventory contains configs/consts. They will be ignored.",
                        file=out,
                    )
                # one csv per object, all obj will be of same model.
                for calib_evt in calibs_qs:
                    # check that inv calibs match part calibs
                    calibs_avail = {
                        cv_set.coefficient_name.calibration_name
                        for cv_set in calib_evt.coefficient_value_sets.all()
                    }
                    print("  <CalibrationEvent: {}>".format(calib_evt), file=out)
                    print(
                        "    calib approved:   {}".format(
                            "PASS" if calib_evt.approved else "FAIL"
                        ),
                        file=out,
                    )
                    print(
                        "    calib validation: {}".format(
                            "PASS"
                            if calibs_to_match.issubset(calibs_avail)
                            else "FAIL. Present={} Missing={}".format(
                                calibs_avail, calibs_to_match - calibs_avail
                            )
                        ),
                        file=out,
                    )
                    if calibs_avail == calibs_to_match and calib_evt.approved:
                        bundle = (calib_evt, None)
                        csv_fname = cls.write_csv(zf, bundle, subdir)
                        print(
                            "SUCCESS:", csv_fname, "zipped!", file=out
                        ) if csv_fname else print(
                            "FAIL:", csv_fname, "is empty", file=out
                        )

            elif not (calibs_to_match or confconsts_to_match):
                print(
                    "FAIL: inv.assembly_part.part does not define any CCCs but inventory has some.",
                    file=out,
                )
                continue

            else:  # config events are expected as per the part definition
                print('MODE: "part has confconsts"', file=out)
                if not configs_by_deployment:
                    print("  FAIL: inventory confconst is empty", file=out)
                for deployment_id, configs_qs in configs_by_deployment.items():
                    depl = Deployment.objects.filter(id=deployment_id).first()
                    depl_date = depl.deployment_to_field_date if depl else None
                    if depl_date:
                        depl_date = depl_date.strftime("%Y-%m-%d")
                    print(
                        '  Deployment: "{}" (id={}, to-field={})'.format(
                            depl, deployment_id, depl_date
                        ),
                        file=out,
                    )
                    if deployment_id is None:
                        print(
                            "    FAIL: conf/const do not have an assigned Deployment",
                            file=out,
                        )
                    elif depl_date is None:
                        print(
                            "    FAIL: conf/const Deployment missing to-field date",
                            file=out,
                        )
                    # check that inv conf/consts match part conf/consts
                    configs_avail = set()
                    approvals = dict()
                    for config_evt in configs_qs:
                        configs_avail.update(
                            [
                                cv.config_name.name
                                for cv in config_evt.config_values.all()
                            ]
                        )
                        approvals[config_evt] = config_evt.approved
                    print(
                        "    conf/consts approved:  {}".format(
                            "PASS"
                            if all(approvals.values())
                            else "FAIL. Approvals={}".format(approvals)
                        ),
                        file=out,
                    )
                    print(
                        "    conf/const validation: {}".format(
                            "PASS"
                            if confconsts_to_match.issubset(configs_avail)
                            else "FAIL. Present={} Missing={}".format(
                                configs_avail, confconsts_to_match - configs_avail
                            )
                        ),
                        file=out,
                    )

                    if not calibs_to_match:
                        if calibs_qs:
                            print(
                                "    WARNING: part does not specify any Calibs but inventory contains some. They will be ignored.",
                                file=out,
                            )
                        print("    calib approved/validation: N/A ", file=out)
                        bundle = (None, *configs_qs)
                    else:
                        cc_date = max([evt.date for evt in configs_qs])
                        calib_evt = calibs_qs.filter(date__lte=cc_date).order_by(
                            "-date", "-id"
                        )
                        if not calib_evt.exists():
                            print("    calib selected: FAIL - None available", file=out)
                            continue
                        calib_evt = calib_evt[0]
                        print(
                            "    calib selected: <CalibrationEvent: {}>".format(
                                calib_evt
                            ),
                            file=out,
                        )
                        calibs_avail = {
                            cv_set.coefficient_name.calibration_name
                            for cv_set in calib_evt.coefficient_value_sets.all()
                        }
                        print(
                            "    calib approved:   {}".format(
                                "PASS" if calib_evt.approved else "FAIL"
                            ),
                            file=out,
                        )
                        print(
                            "    calib validation: {}".format(
                                "PASS"
                                if calibs_to_match.issubset(calibs_avail)
                                else "FAIL. Present={} Missing={}".format(
                                    calibs_avail, calibs_to_match - calibs_avail
                                )
                            ),
                            file=out,
                        )
                        bundle = (calib_evt, *configs_qs)

                        if not calib_evt.approved:
                            continue
                        if not calibs_to_match.issubset(calibs_avail):
                            continue
                    if deployment_id is None:
                        continue
                    if depl_date is None:
                        continue
                    if not all(approvals.values()):
                        continue
                    if not confconsts_to_match.issubset(configs_avail):
                        continue
                    csv_fname = cls.write_csv(zf, bundle, subdir)
                    print(
                        "SUCCESS:", csv_fname, "zipped!", file=out
                    ) if csv_fname else print("FAIL:", csv_fname, "is empty", file=out)

        if isinstance(verbose, str):
            print("\n", file=out)  # final newline
            zf.writestr(verbose, out.getvalue())
            out.close()

    @classmethod
    def write_csv(cls, zf, bundle, subdir=None):
        fname_obj = bundle[1] or bundle[0]  # new config/const are found in bundle[1]
        try:
            fname_date = fname_obj.deployment.deployment_to_field_date.strftime(
                "%Y%m%d"
            )
        except AttributeError:
            fname_date = fname_obj.date.strftime("%Y%m%d")
        csv_fname = "{}__{}.csv".format(fname_obj.inventory.serial_number, fname_date)
        csv_content = io.StringIO()
        csv_writer = CSV.writer(csv_content)
        header = ["serial", "name", "value", "notes"]
        has_content = None
        csv_writer.writerow(header)

        for obj in bundle:
            if isinstance(obj, CalibrationEvent):
                # Reference to Calibrations-Only Class
                rows, aux_files = ExportCalibrationEvents.get_csvrows_aux(obj)
                if rows:
                    has_content = True
                csv_writer.writerows(rows)
                for extra_fname, extra_content in aux_files:
                    if subdir:
                        extra_fname = join(subdir, extra_fname)
                    cls.zf_safewrite(zf, extra_fname, extra_content, mode="count")

            elif isinstance(obj, ConfigEvent):
                # Reference to Configs-Only Class
                rows = ExportConfigEvents.get_csvrows(obj, export_with_calibs_only=True)
                if rows:
                    has_content = True
                csv_writer.writerows(rows)

        # write csv to zip
        if subdir:
            csv_fname = join(subdir, csv_fname)
        if has_content:  # avoid blank files
            cls.zf_safewrite(zf, csv_fname, csv_content.getvalue(), mode="count")
            return csv_fname
        else:
            return None


# Cruises CSV
class ExportCruises(CSVExport):
    model = Cruise
    fname = "CruiseInformation.csv"
    ordering = ["cruise_start_date"]
    # see https://github.com/oceanobservatories/asset-management/tree/master/cruise

    @classmethod
    def build_csv(cls, csv, objs, CI_mode=False):
        objs = objs.prefetch_related("vessel")
        if CI_mode == True:
            headers = [
                "CUID",
                "ShipName",
                "cruiseStartDateTime",
                "cruiseStopDateTime",
                "notes",
            ]
        else:
            headers = [
                "CUID",
                "ShipName",
                "Friendly Name",
                "Destination",
                "cruiseStartDateTime",
                "cruiseStopDateTime",
                "notes",
            ]

        csv.writerow(headers)
        for cruise in objs:
            row = list()
            location = cruise.location or ""
            notes = cruise.notes or ""
            row.append(cruise.CUID)
            row.append(getattr(cruise.vessel, "vessel_name", ""))
            if CI_mode == False:
                row.append(cruise.friendly_name)
            if CI_mode == False:
                row.append(location)
            row.append(cruise.cruise_start_date.replace(tzinfo=None).isoformat())
            row.append(cruise.cruise_stop_date.replace(tzinfo=None).isoformat())
            row.append(notes)
            csv.writerow(row)


# Vessels CSV
class ExportVessels(CSVExport):
    model = Vessel
    fname = "shiplist.csv"
    ordering = ["prefix"]
    # see https://github.com/oceanobservatories/asset-management/tree/master/vessel
    header_att = [
        ("Prefix", "prefix"),
        ("Vessel Designation", "vessel_designation"),
        ("Vessel Name", "vessel_name"),
        ("ICES Code", "ICES_code"),
        ("Operator", "operator"),
        ("Call Sign", "call_sign"),
        ("MMSI#", "MMSI_number"),
        ("IMO#", "IMO_number"),
        ("Length (m)", "length"),
        ("Max Speed (m/s)", "max_speed"),
        ("Max Draft (m)", "max_draft"),
        ("Designation", "designation"),
        ("Active", "active"),
        ("R2R", "R2R"),
    ]

    @classmethod
    def build_csv(cls, csv, objs, CI_mode=False):
        header_att = cls.header_att.copy()
        if CI_mode == False:
            header_att.append(("Notes", "notes"))

        headers, attribs = zip(*header_att)
        csv.writerow(headers)
        for vessel in objs:
            row = []
            for att in attribs:
                val = getattr(vessel, att, None)
                if val is None:
                    val = ""
                elif isinstance(val, bool):
                    val = "Y" if val else "N"
                    if att == "active" and val == "N":
                        val = "(N)"
                row.append(str(val))
            csv.writerow(row)

# Reference Designators CSV
class ExportReferenceDesignators(CSVExport):
    model = ReferenceDesignator
    fname = "refdes.csv"
    ordering = ["refdes_name"]
    # see https://github.com/oceanobservatories/asset-management/tree/master/vocab
    header_att = [
        ("Reference_Designator", "refdes_name"),
        ("TOC_L1", "toc_l1"),
        ("TOC_L2", "toc_l2"),
        ("TOC_L3", "toc_l3"),
        ("Instrument", "instrument"),
        ("Manufacturer", "manufacturer"),
        ("Model", "model"),
        ("Min Depth", "min_depth"),
        ("Max Depth", "max_depth")
    ]

    @classmethod
    def build_csv(cls, csv, objs, CI_mode=False):
        header_att = cls.header_att.copy()
        
        headers, attribs = zip(*header_att)
        csv.writerow(headers)
        for refdes in objs:
            row = []
            for att in attribs:
                val = getattr(refdes, att, None)
                if val is None:
                    val = ""
                row.append(str(val))
            csv.writerow(row)

# Inventory Bulk CSV
class ExportInventory(CSVExport):
    model = Inventory
    fname = "Inventory.csv"
    # see https://github.com/oceanobservatories/asset-management/tree/master/bulk
    header_att = [
        ("ASSET_UID", "serial_number"),  # Inventory
        ("LEGACY_ASSET_UID", "old_serial_number"), # not populated
        ("TYPE", ""),
        ("Mobile", ""),
        ("DESCRIPTION OF EQUIPMENT", ""),
        ("MIO_Inventory_Description", ""),
        ("Manufacturer", "Manufacturer"),  # Custom Fields
        ("Model", "Model"),
        ("Manufacturer's Serial No./Other Identifier", "Manufacturer Serial Number"),
        ("Firmware Version", "Firmware Version"),
        ("ACQUISITION DATE", ""),
        ("ORIGINAL COST", ""),
        ("comments", ""),
        ("MIO", ""),
        ("RDB_Part_Template", "part")  # Inventory
    ]

    @classmethod
    def build_csv(cls, csv, objs, CI_mode=False):
        header_att = cls.header_att.copy()
        
        headers, attribs = zip(*header_att)
        csv.writerow(headers)

        for inventory in objs:
            # Get the Model, Manufacturer, Manufacturer Serial Number, Firmware Version
            model_value = inventory.fieldvalues.filter(is_current=True, field__field_name="Model") \
                          .values_list("field_value", flat=True).first()
            manu_value = inventory.fieldvalues.filter(is_current=True, field__field_name="Manufacturer") \
                          .values_list("field_value", flat=True).first()
            serial_value = inventory.fieldvalues.filter(is_current=True, field__field_name="Manufacturer Serial Number") \
                          .values_list("field_value", flat=True).first()
            firmware_value = inventory.fieldvalues.filter(is_current=True, field__field_name="Firmware Version") \
                          .values_list("field_value", flat=True).first()

            row = []
            for att in attribs:
                if att == "Model":
                    val = model_value
                    print("model_value: ", model_value, flush=True)
                elif att == "Manufacturer":
                    val = manu_value
                    print("manu_value: ", manu_value, flush=True)
                elif att == "Manufacturer Serial Number":
                    val = serial_value
                    print("serial_value: ", serial_value, flush=True)
                elif att == "Firmware Version":
                    val = firmware_value
                    print("firmware_value: ", firmware_value, flush=True)
                elif att == "part":
                    val = inventory.part.part_number if inventory.part else None
                    print("val :", val, flush=True)
                else:
                    val = getattr(inventory, att, None)
                    print("val :",val, flush=True)
                if val is None:
                    val = ""
                row.append(str(val))
            csv.writerow(row)


# Deployment Bulk Export
class ExportDeployments(ZipExport):
    model = Deployment
    fname = "Deployments.zip"
    # header att are for InventoryDeployment objects
    header_att = [
        ("CUID_Deploy", "cruise_deployed"),  # DeploymentBase
        ("deployedBy", ""),  # todo text field
        ("CUID_Recover", "cruise_recovered"),  # DeploymentBase
        ("recoveredBy", ""),  # todo text field
        ("Reference Designator", "assembly_part.reference_designator"),
        ("deploymentNumber", "deployment.deployment_number"),
        ("versionNumber", "1"),  # always1
        ("startDateTime", "deployment_to_field_date"),  # DeploymentBase
        ("stopDateTime", "deployment_recovery_date"),  # DeploymentBase
        ("mooring.uid", ""),
        ("node.uid", ""),
        ("sensor.uid", "inventory.serial_number"),
        ("lat", "deployment.latitude"),
        ("lon", "deployment.longitude"),
        ("orbit", ""),
        ("deployment_depth", "deployment.config_event('Nominal_Depth').config_value"),
        ("water_depth", "deployment.depth"),
        ("notes", "inventory.detail"),  # alternatively, "assembly_part.note"
        ("electrical.uid", ""),
        (
            "assembly_template_revision",
            "assembly_part.assembly_revision.revision_code",
        ),  # or blank
    ]

    @classmethod
    def build_zip(cls, zf, objs, subdir=None):
        headers, attribs = zip(*cls.header_att)

        def depl_row(depl_obj, attribs):
            row = []
            for att in attribs:
                if att == "1":
                    val = 1  # versionNumber
                elif att == "deployment.config_event('Nominal_Depth').config_value":
                    # Step 1: Retrieve ConfigName, with check for None
                    config_name = ConfigName.objects.filter(
                        name="Nominal Depth",
                        part=depl_obj.inventory.part,
                        config_type="conf",
                    ).first()
                    
                    if config_name is None:
                        # If ConfigName is missing, set a default/fallback value
                        val = "N/A"
                    else:
                        # Step 2: Retrieve ConfigEvent, with check for None
                        config_event = ConfigEvent.objects.filter(
                            inventory=depl_obj.inventory, deployment=depl_obj.deployment
                        ).first()
                        
                        if config_event is None:
                            # If ConfigEvent is missing, set a default/fallback value
                            val = "N/A"
                        else:
                            # Step 3: Retrieve ConfigValue, with check for None
                            config_val = ConfigValue.objects.filter(
                                config_event=config_event, config_name=config_name
                            ).first()
                            
                            # If ConfigValue is found, use config_value; if not, use "N/A"
                            val = config_val.config_value if config_val else "N/A"
                else:
                    # Fallback for other attributes
                    try:
                        val = attrgetter(att)(depl_obj)
                    except AttributeError:
                        val = None

                # Additional formatting for specific types
                if isinstance(val, dt.datetime):  # dates
                    val = val.replace(
                        tzinfo=None
                    )  # remove timezone awareness
                    val = val.isoformat(
                        timespec="seconds"
                    )  # format datetime as ISO string
                elif isinstance(val, float):  # lat, lon
                    val = "{:.5f}".format(val)
                elif att in ["cruise_deployed", "cruise_recovered"] and not val:
                    # If CUID_deployed/recovered not recorded on InventoryDeployment, check parent deployment
                    try:
                        val = attrgetter("deployment." + att)(depl_obj)
                    except AttributeError:
                        val = None

                # Final fallback for None values
                val = str(val) if val is not None else ""

                row.append(val)
            return row


        objs = objs.prefetch_related("build__assembly_revision__assembly")
        assy_names = objs.values_list(
            "build__assembly_revision__assembly__name", flat=True
        )
        assy_names = set(assy_names)
        assy_names.discard(None)  # removes None if any
        for assy_name in assy_names:
            csv_fname = "{}_Deploy.csv".format(str(assy_name).replace(" ", "_"))
            if subdir:
                csv_fname = join(subdir, csv_fname)
            csv_content = io.StringIO()
            csv = CSV.writer(csv_content)
            csv.writerow(headers)
            for depl in objs.filter(
                build__assembly_revision__assembly__name__exact=assy_name
            ):
                # row = depl_row(depl,attribs)
                # csv.writerow(row)
                for inv_depl in depl.inventory_deployments.all():
                    row = depl_row(inv_depl, attribs)
                    csv.writerow(row)
            cls.zf_safewrite(zf, csv_fname, csv_content.getvalue())


# Bulk Export Combo!!
class ExportCI(ZipExport):
    model = None
    fname = "asset-management.zip"

    def get_queryset(self):
        return None

    @classmethod
    def build_zip(cls, zf, objs):
        # Deployment csv's
        deployments = Deployment.objects.all()
        ExportDeployments.build_zip(zf, deployments, subdir="deployment")

        # Calibration csv's
        ccc = ExportCalibrationEvents_withConfigs.get_queryset()
        ExportCalibrationEvents_withConfigs.build_zip(zf, ccc, subdir="calibration")

        # Cruises csv
        cruises = Cruise.objects.all()
        cruise_csv_fname = join("cruise", ExportCruises.fname)
        cruise_csv_content = io.StringIO()
        cruise_csv = CSV.writer(cruise_csv_content)
        ExportCruises.build_csv(cruise_csv, cruises, CI_mode=True)
        zf.writestr(cruise_csv_fname, cruise_csv_content.getvalue())
        cruise_csv_content.close()

        # Vessels csv
        vessels = Vessel.objects.all()
        vessel_csv_fname = join("vessel", ExportVessels.fname)
        vessel_csv_content = io.StringIO()
        vessel_csv = CSV.writer(vessel_csv_content)
        ExportVessels.build_csv(vessel_csv, vessels, CI_mode=True)
        zf.writestr(vessel_csv_fname, vessel_csv_content.getvalue())
        vessel_csv_content.close()


# OBS Builds
# TODO might need to furthermore limit to builds of the same assembly THAT ARE IN THE SAME LOCATION
class ExportOBSAssemblyBuilds(DetailView, LoginRequiredMixin):
    model = Assembly
    context_object_name = "assm"

    def render_to_response(self, context, **response_kwargs):
        assm = context.get(self.context_object_name)  # getting object from context
        fname = self.get_filename(assm)

        # Reference to other bulk export class
        rows = self.get_csvrows(assm)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'inline; filename="{}"'.format(fname)
        writer = CSV.writer(response)
        writer.writerows(rows)
        return response

    @staticmethod
    def get_filename(assm):
        return f"{assm.name}.csv"

    @staticmethod
    def get_csvrows(assm, location=None, skip_retired=True, skip_trashed=True):
        objs = assm.builds  # fetch all builds associated with assembly
        if location:
            objs = objs.filter(location=location)
        objs = objs.prefetch_related(
            "inventory", "deployments", "inventory__assembly_part"
        )

        # collect data
        data = {}
        promoted_headers = [
            "System #",
            "Notes",
            "Location",
            "Deployment Number",
            "Surveyed Lat",
            "Surveyed Lon",
            "Drop Lat",
            "Drop Lon",
            "Surveyed Depth",
            "Drop Depth",
        ]

        def field_safeget(vals, fieldname):
            try:
                return vals.get(field__field_name=fieldname).field_value
            except FieldValue.DoesNotExist:
                return "-"

        def nested_update(dic, keys, row_num, row_val):
            # This is used to build a dict tree structure for assembly parts to maintain their tree ordering for csv export
            # Data for an assembly-part column is saved under "rows" and any other key is a new subassemblypart dict
            # Rows are saved with an associated row_number to account for any missing data row data in a column.
            # nested_unpack2cols() later unfolds this data structure into flat columnar data with proper ordering
            for key in keys + ["rows"]:
                if key not in dic:
                    dic[key] = {}
                dic = dic[key]
            dic.update({row_num: str(row_val)})

        row_num = 0
        for build in objs:
            if (
                not location
                and skip_retired
                and build.location.get_root().root_type == "Retired"
            ):
                continue
            if (
                not location
                and skip_trashed
                and build.location.get_root().root_type == "Trash"
            ):
                continue
            row_num += 1
            depl = build.deployments.latest() if build.deployments.exists() else None
            depl = (
                depl
                if depl and depl.current_status == Deployment.DEPLOYMENTTOFIELD
                else None
            )

            nested_update(data, ["System #"], row_num, build.build_number)
            nested_update(data, ["Notes"], row_num, build.build_notes)
            nested_update(data, ["Location"], row_num, build.location)
            nested_update(
                data,
                ["Deployment Number"],
                row_num,
                depl.deployment_number if depl else "",
            )
            nested_update(
                data, ["Surveyed Lat"], row_num, depl.surveyed_latitude if depl else ""
            )
            nested_update(
                data, ["Surveyed Lon"], row_num, depl.surveyed_longitude if depl else ""
            )
            nested_update(data, ["Drop Lat"], row_num, depl.latitude if depl else "")
            nested_update(data, ["Drop Lon"], row_num, depl.longitude if depl else "")
            nested_update(
                data, ["Surveyed Depth"], row_num, depl.surveyed_depth if depl else ""
            )
            nested_update(data, ["Drop Depth"], row_num, depl.depth if depl else "")

            inv_lineage_keylist = []

            for inv in build.inventory.all():
                sn = inv.serial_number
                try:
                    inv_lineage = inv.assembly_part.get_ancestors(include_self=True)
                except:
                    continue

                inv_lineage_keys = [
                    normalize("NFKD", str(asspart)) for asspart in inv_lineage
                ]
                part = inv_lineage_keys[-1]

                duplicate_count = inv_lineage_keylist.count(inv_lineage_keys)
                uniquifier_postfix = " " * duplicate_count
                inv_lineage_keylist.append(inv_lineage_keys.copy())
                inv_lineage_keys[-1] += uniquifier_postfix

                nested_update(data, inv_lineage_keys, row_num, sn)

                if part.startswith("PCB, Acoustic Release"):
                    vals = inv.fieldvalues.filter(is_current=True)
                    ar_enable = vals.get(
                        field__field_name__icontains="Enable"
                    ).field_value
                    ar_disable = vals.get(
                        field__field_name__icontains="Disable"
                    ).field_value
                    ar_burn1 = vals.get(
                        field__field_name__icontains="Burn 1"
                    ).field_value
                    ar_option = vals.get(
                        field__field_name__icontains="Option"
                    ).field_value
                    nested_update(
                        data, inv_lineage_keys + [" Enable"], row_num, ar_enable
                    )
                    nested_update(
                        data, inv_lineage_keys + [" Disable"], row_num, ar_disable
                    )
                    nested_update(
                        data, inv_lineage_keys + [" Burn1"], row_num, ar_burn1
                    )
                    nested_update(
                        data, inv_lineage_keys + [" Option"], row_num, ar_option
                    )

                elif part.startswith("Q330"):
                    vals = inv.fieldvalues.filter(is_current=True)
                    q330_idsn = field_safeget(vals, "Q330 Tag ID / SN")
                    q330_lsn = field_safeget(vals, "Q330 Long Serial Number")
                    q330_ip = field_safeget(vals, "Q330 IP")
                    nested_update(
                        data,
                        inv_lineage_keys + [" Q330: Tag ID/SN"],
                        row_num,
                        q330_idsn,
                    )
                    nested_update(
                        data, inv_lineage_keys + [" Q330: Long S/N"], row_num, q330_lsn
                    )
                    nested_update(
                        data, inv_lineage_keys + [" Q330: IP"], row_num, q330_ip
                    )

                elif part.startswith("Baler 14"):
                    vals = inv.fieldvalues.filter(is_current=True)
                    baller_tag = field_safeget(vals, "Baler Tag")
                    nested_update(
                        data, inv_lineage_keys + [" Baler 14: Tag"], row_num, baller_tag
                    )

        # format data to rows
        def nested_unpack2cols(d):
            # unpacks the nested_update dict to appropriately-ordered columnar data
            for header, v in d.items():
                # the rows for a column are extracted, filled in for missing data, and ordered
                rows = v.pop("rows", {})
                for i in range(1, row_num + 1):
                    if i not in rows:
                        rows[i] = "-"
                rows = [value for (key, value) in sorted(rows.items())]
                # column headers and rows are then recursively yielded
                for subheader, v2 in nested_unpack2cols(v):
                    yield (header,) + subheader, v2
                yield (header,), rows

        cols = []
        priority_cols = []
        for p, v in nested_unpack2cols(data):
            if p[-1] in promoted_headers:
                priority_cols.append((p, v))
            else:
                cols.append((p, v))

        cols_sorted = sorted(cols, key=lambda x: x[0])
        cols_combo = priority_cols + cols_sorted
        cols_final = [[p[-1]] + v for p, v in cols_combo]

        rows = list(zip(*cols_final))

        return rows


class ExportOBSBuildsAll(ZipExport):
    model = Assembly
    fname = "OBSBuilds.zip"

    @classmethod
    def build_zip(cls, zf, objs, subdir=None):
        for assm in objs:
            csv_fname = ExportOBSAssemblyBuilds.get_filename(assm)

            if subdir:
                csv_fname = join(subdir, csv_fname)

            rows = ExportOBSAssemblyBuilds.get_csvrows(assm)

            # if an assembly has no builds, ignore it
            if len(rows) < 2:
                continue

            csv_content = io.StringIO()
            writer = CSV.writer(csv_content)
            writer.writerows(rows)
            cls.zf_safewrite(zf, csv_fname, csv_content.getvalue())
