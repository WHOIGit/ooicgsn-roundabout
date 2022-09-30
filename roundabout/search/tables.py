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
from random import randint

import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html, mark_safe, strip_tags
from django.utils.text import Truncator
from django_tables2.columns import Column, DateColumn, DateTimeColumn, ManyToManyColumn
from django_tables2_column_shifter.tables import ColumnShiftTable

from roundabout.assemblies.models import Assembly, AssemblyPart
from roundabout.builds.models import Build
from roundabout.calibrations.models import CalibrationEvent, CoefficientNameEvent
from roundabout.configs_constants.models import (
    ConfigEvent,
    ConstDefaultEvent,
    ConfigNameEvent,
    ConfigDefaultEvent,
)
from roundabout.inventory.models import (
    Inventory,
    Action,
    Deployment,
    InventoryDeployment,
    InventoryTestResult,
)
from roundabout.parts.models import Part
from roundabout.cruises.models import Vessel, Cruise
from roundabout.ooi_ci_tools.models import ReferenceDesignatorEvent


def trunc_render(
    length=100, safe=False, showable=True, hideable=True, targets=None, bold_target=True
):
    def boldify(text, target):
        if target and target.lower() in text.lower():
            target_idx = text.lower().index(target.lower())
            text = (
                text[:target_idx]
                + "<strong><em>"
                + text[target_idx : target_idx + len(target)]
                + "</em></strong>"
                + text[target_idx + len(target) :]
            )
            return text
        else:
            return text

    def render_func(value):

        if targets and isinstance(targets, list):  # just use the first match
            target = [
                t for t in targets if isinstance(t, str) and t.lower() in value.lower()
            ]
            if target:
                target = target[0]
            else:
                target = None
        else:
            target = targets

        if len(value) <= length:
            if bold_target:
                output_str = boldify(value, target)
            else:
                output_str = value
        else:
            if target and target.lower() in value.lower():
                value_stripped = strip_tags(value)
                target_idx = value_stripped.lower().index(target.lower())
                start_idx, end_idx = target_idx - int(length / 2), target_idx + int(
                    length / 2
                )
                start_idx, end_idx = start_idx + int(len(target) / 2), end_idx + int(
                    len(target) / 2
                )
                if start_idx > 0 and end_idx < len(value_stripped):
                    shown_txt = value_stripped[start_idx:end_idx]
                    start, end = "▴…", "…▾"
                elif end_idx > len(value):
                    shown_txt = value_stripped[-length:]
                    start, end = "▴…", ""
                else:
                    shown_txt = Truncator(value).chars(length, "", html=True)
                    start, end = "", "…▾"

                if bold_target:
                    shown_txt = boldify(shown_txt, target)

            else:
                start, end = "", "…▾"
                shown_txt = Truncator(value).chars(length, "", html=True)

            if showable:  # insert some javascript to show truncated text
                unshow_txt = " …▴" if hideable else ""
                hidden_id = "trunc{:05}".format(randint(0, 100000))
                hidden_txt = value  # all of it
                if bold_target:
                    hidden_txt = boldify(hidden_txt, target)
                onclick_show = 'document.getElementById("{id}-full").style.display="inline";document.getElementById("{id}").style.display="none"; return false;'.format(
                    id=hidden_id
                )
                onclick_hide = 'document.getElementById("{id}-full").style.display="none";document.getElementById("{id}").style.display="inline"; return false;'.format(
                    id=hidden_id
                )
                a_start = (
                    """<a href="#" onclick='{oc}'>{text}</a>""".format(
                        oc=onclick_show, text=start
                    )
                    if start
                    else ""
                )
                a_end = (
                    """<a href="#" onclick='{oc}'>{text}</a>""".format(
                        oc=onclick_show, text=end
                    )
                    if end
                    else ""
                )
                a_unshow = (
                    """<a href="#" onclick='{oc}'>{text}</a>""".format(
                        oc=onclick_hide, text=unshow_txt
                    )
                    if unshow_txt
                    else ""
                )
                shown_html = """<div id="{id}">{a_start}{text}{a_end}</div>""".format(
                    id=hidden_id,
                    text=shown_txt,
                    oc=onclick_show,
                    a_start=a_start,
                    a_end=a_end,
                )
                hidden_html = '<div id="{id}-full" style="display:none;">{text}{a_unshow}</div>'.format(
                    id=hidden_id, text=hidden_txt, a_unshow=a_unshow
                )
                shown_html = mark_safe(shown_html)
                hidden_html = mark_safe(hidden_html)
                output_str = shown_html + hidden_html

            else:
                output_str = start + shown_txt + end

        if safe:
            output_str = mark_safe(output_str)
        return output_str

    return render_func


class UDF_Column(ManyToManyColumn):
    prefix = "udf-"

    def __init__(
        self,
        udf,
        accessor,
        accessor_type=["Field", "FieldValue"][0],
        footer_count=False,
        **kwargs
    ):
        self.udf = udf
        self.accessor = accessor
        self.accessor_type = accessor_type
        if accessor_type == "Field":
            col_name = "{} (Default)".format(udf.field_name)
            udf_filter = self.field_filter
        else:  # FieldValue
            col_name = udf.field_name
            udf_filter = self.fieldvalues_filter

        if footer_count:
            footer = self.footer_filter
        else:
            footer = None

        super().__init__(
            accessor=accessor,
            verbose_name=col_name,
            orderable=True,
            default="",
            filter=udf_filter,
            footer=footer,
            **kwargs
        )

    def field_filter(self, qs):
        qs = qs.filter(id=self.udf.id)
        if qs:
            return [qs[0].field_default_value]
        else:
            return ["n/a"]

    def fieldvalues_filter(self, qs):
        return qs.filter(field__id=self.udf.id, is_current=True)

    def footer_filter(self, table):
        # quite expensive to run. Activated with GET flag "show-udf-footer-count"
        field = (
            "id" if self.accessor_type == "Field" else "field__id"
        )  # for 'FieldValue'
        udf_vals = [
            getattr(row, self.accessor).filter(**{field: self.udf.id})
            for row in table.data
        ]
        return len([val for val in udf_vals if val])


class SearchTable(ColumnShiftTable):
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        fields = []
        base_shown_cols = []
        attrs = {"style": "display: block; overflow-x: auto;"}

    def set_column_default_show(self, table_data):
        if not self.Meta.base_shown_cols:
            self.column_default_show = None
        else:
            search_cols = [col for col in self.sequence if col.startswith("searchcol-")]
            extra_cols = [col for col in self.sequence if col.startswith("extracol-")]
            self.column_default_show = self.Meta.base_shown_cols + search_cols

    def render_detail(self, value):
        return trunc_render()(value)


class InventoryTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Inventory
        udf_accessors = ["fieldvalues__field__field_name", "fieldvalues__field_value"]
        base_shown_cols = ["serial_number", "part__name", "location__name"]

    def set_column_default_show(self, table_data):
        search_cols = [col for col in self.sequence if col.startswith("searchcol-")]
        extra_cols = [col for col in self.sequence if col.startswith("extracol-")]
        udf_cols = [
            col
            for col in self.sequence
            if col.startswith(UDF_Column.prefix)
            or col.startswith("searchcol-" + UDF_Column.prefix)
        ]
        self.column_default_show = self.Meta.base_shown_cols + search_cols


class PartTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Part
        base_shown_cols = ["part_number", "name", "part_type__name"]

    def set_column_default_show(self, table_data):
        search_cols = [col for col in self.sequence if col.startswith("searchcol-")]
        extra_cols = [col for col in self.sequence if col.startswith("extracol-")]
        udf_cols = [
            col
            for col in self.sequence
            if col.startswith(UDF_Column.prefix)
            or col.startswith("searchcol-" + UDF_Column.prefix)
        ]
        self.column_default_show = self.Meta.base_shown_cols + search_cols


class BuildTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Build
        base_shown_cols = [
            "build",
            "assembly__assembly_type__name",
            "location__name",
            "time_at_sea",
            "is_deployed",
        ]

    build = Column(
        empty_values=(),
        order_by=("assembly__assembly_number", "build_number"),
        attrs={"style": "white-space: nowrap;"},
    )

    def render_build(self, record):
        item_url = reverse("builds:builds_detail", args=[record.pk])
        ass_num = record.assembly.assembly_number or record.assembly.name
        html_string = "<a href={}>{}-{}</a>".format(
            item_url, ass_num, record.build_number.replace("Build ", "")
        )
        return format_html(html_string)

    def value_build(self, record):
        return "{}-{}".format(
            record.assembly.assembly_number, record.build_number.replace("Build ", "")
        )


class AssemblyTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Assembly
        base_shown_cols = ["name", "assembly_type__name", "description"]


class ActionTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Action
        fields = [
            "object_type",
            "object",
            "action_type",
            "user",
            "created_at",
            "detail",
        ]  # ,'data']
        base_shown_cols = fields

    object = Column(verbose_name="Associated Object", accessor="object_type")

    def value_object(self, record):
        parent_obj = record.get_parent()
        if isinstance(parent_obj, (CalibrationEvent, ConfigEvent, ConstDefaultEvent)):
            parent_obj = parent_obj.inventory
        elif isinstance(parent_obj, (ConfigNameEvent, CoefficientNameEvent)):
            parent_obj = parent_obj.part
        elif isinstance(parent_obj, ConfigDefaultEvent):
            parent_obj = parent_obj.assembly_part
        return str(parent_obj)

    def render_object(self, record):
        html_string = "<a href={url}>{text}</a>"
        parent_obj = record.get_parent()
        if isinstance(parent_obj, (CalibrationEvent, ConfigEvent, ConstDefaultEvent)):
            parent_obj = parent_obj.inventory
        elif isinstance(parent_obj, (ConfigNameEvent, CoefficientNameEvent)):
            parent_obj = parent_obj.part
        elif isinstance(parent_obj, ConfigDefaultEvent):
            parent_obj = parent_obj.assembly_part

        if isinstance(parent_obj, Inventory):
            inv_url = reverse("inventory:inventory_detail", args=[parent_obj.pk])
            html_string = html_string.format(url=inv_url, text=parent_obj)
        elif isinstance(parent_obj, Build):
            build_url = reverse("builds:builds_detail", args=[parent_obj.pk])
            html_string = html_string.format(url=build_url, text=parent_obj)
        elif isinstance(parent_obj, Deployment):
            try:
                build_url = reverse(
                    "builds:builds_detail", args=[record.deployment.build.pk]
                )
                deployment_anchor = "#deployment-{}-".format(
                    record.deployment.pk
                )  # doesn't work, anchor doesn't exist
                deployment_anchor = "#deployments"  # next best anchor that does work
                html_string = html_string.format(
                    url=build_url + deployment_anchor, text=parent_obj
                )
            except AttributeError:  # MANIFEST error, from import?
                html_string = str(parent_obj)
        elif isinstance(parent_obj, InventoryDeployment):
            inv_url = reverse(
                "inventory:inventory_detail", args=[parent_obj.inventory.pk]
            )
            html_string = html_string.format(url=inv_url, text=parent_obj)
        elif isinstance(parent_obj, Part):
            build_url = reverse("parts:parts_detail", args=[parent_obj.pk])
            html_string = html_string.format(url=build_url, text=parent_obj)
        elif isinstance(parent_obj, AssemblyPart):
            assy_url = reverse("assemblies:assemblypart_detail", args=[parent_obj.pk])
            html_string = html_string.format(url=assy_url, text=parent_obj)
        elif isinstance(parent_obj, Vessel):
            vessel_url = reverse("cruises:vessels_home")
            html_string = html_string.format(url=vessel_url, text=parent_obj)
        elif isinstance(parent_obj, Cruise):
            cruise_url = reverse("cruises:cruises_detail", args=[parent_obj.pk])
            html_string = html_string.format(url=cruise_url, text=parent_obj)
        elif isinstance(parent_obj, ReferenceDesignatorEvent):
            html_string = str(parent_obj.reference_designator)
        else:
            html_string = ""

        if html_string:
            return format_html(html_string)
        return ""


class CalibrationTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = CalibrationEvent
        fields = [
            "inventory__serial_number",
            "inventory__part__name",
            "inventory__location",
            "calibration_date",
            "deployment",
            "approved",
            "user_approver__all__name",
            "user_draft__all__name",
            "created_at",
        ]
        base_shown_cols = ["inventory__serial_number", "calibration_date", "approved"]

    inventory__serial_number = Column(
        verbose_name="Inventory SN",
        attrs={"style": "white-space: nowrap;"},
        linkify=dict(
            viewname="inventory:inventory_detail", args=[tables.A("inventory__pk")]
        ),
    )
    inventory__part__name = Column(
        verbose_name="Part",
        linkify=dict(
            viewname="parts:parts_detail", args=[tables.A("inventory__part__pk")]
        ),
    )
    calibration_date = DateColumn(
        verbose_name="Calibration Date",
        format="Y-m-d",
        linkify=dict(viewname="exports:calibration", args=[tables.A("pk")]),
    )

    user_approver__all__name = ManyToManyColumn(
        verbose_name="Approvers",
        accessor="user_approver",
        transform=lambda x: x.name or x.username,
        default="",
    )
    user_draft__all__name = ManyToManyColumn(
        verbose_name="Reviewers",
        accessor="user_draft",
        transform=lambda x: x.name or x.username,
        default="",
    )

    coefficient_value_set__names = ManyToManyColumn(
        verbose_name="Coefficient Names",
        accessor="coefficient_value_sets",
        transform=lambda x: x.coefficient_name,
        separator="; ",
    )
    coefficient_value_set__values = ManyToManyColumn(
        verbose_name="Coefficient Values",
        accessor="coefficient_value_sets",
        transform=lambda x: trunc_render(37)(x.value_set),
        separator="; ",
    )
    coefficient_value_set__notes = ManyToManyColumn(
        verbose_name="Coefficient Notes",
        accessor="coefficient_value_sets",
        transform=lambda x: format_html(
            "<b>{}:</b> [{}]<br>".format(x.coefficient_name, trunc_render()(x.notes))
        )
        if x.notes
        else "",
        separator="\n",
    )

    detail = Column(verbose_name="CalibrationEvent Note", accessor="detail")
    created_at = DateTimeColumn(
        verbose_name="Date Entered", accessor="created_at", format="Y-m-d H:i"
    )

    refdes = Column(
        verbose_name="Reference Designator",
        accessor="inventory__assembly_part__reference_designator__refdes_name",
    )

    def value_coefficient_value_set__values(self, value):
        return "; ".join([str(val) for val in value.all()])

    def value_coefficient_value_set__notes(self, value):
        notes = []
        for val in value.all():
            if val.notes:
                note = "{}: [{}]".format(val.coefficient_name, val.notes)
                notes.append(note)
        return "\n".join(notes)


class ConfigConstTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = ConfigEvent
        fields = [
            "inventory__serial_number",
            "inventory__part__name",
            "inventory__location",
            "config_type",
            "configuration_date",
            "deployment",
            "approved",
            "user_approver__all__name",
            "user_draft__all__name",
            "created_at",
        ]
        base_shown_cols = [
            "inventory__serial_number",
            "configuration_date",
            "config_type",
            "approved",
        ]

    inventory__serial_number = Column(
        verbose_name="Inventory SN",
        attrs={"style": "white-space: nowrap;"},
        linkify=dict(
            viewname="inventory:inventory_detail", args=[tables.A("inventory__pk")]
        ),
    )
    inventory__part__name = Column(
        verbose_name="Part",
        linkify=dict(
            viewname="parts:parts_detail", args=[tables.A("inventory__part__pk")]
        ),
    )
    config_type = Column(verbose_name="Type")
    configuration_date = DateColumn(
        verbose_name="Event Date",
        format="Y-m-d",
        linkify=dict(viewname="exports:configconst", args=[tables.A("pk")]),
    )
    user_approver__all__name = ManyToManyColumn(
        verbose_name="Approvers",
        accessor="user_approver",
        transform=lambda x: x.name or x.username,
        default="",
    )
    user_draft__all__name = ManyToManyColumn(
        verbose_name="Reviewers",
        accessor="user_draft",
        transform=lambda x: x.name or x.username,
        default="",
    )

    config_values__names = ManyToManyColumn(
        verbose_name="Config/Constant Names",
        accessor="config_values",
        transform=lambda x: x.config_name,
        separator="; ",
    )
    config_values__values = ManyToManyColumn(
        verbose_name="Config/Constant Values",
        accessor="config_values",
        transform=lambda x: x.config_value,
        separator="; ",
    )
    config_values__notes = ManyToManyColumn(
        verbose_name="Config/Constant Notes",
        accessor="config_values",
        transform=lambda x: format_html(
            "<b>{}:</b> [{}]<br>".format(x.config_name, trunc_render()(x.notes))
        )
        if x.notes
        else "",
        separator="\n",
    )

    detail = Column(verbose_name="ConfigEvent Note", accessor="detail")
    created_at = DateTimeColumn(
        verbose_name="Date Entered", accessor="created_at", format="Y-m-d H:i"
    )

    refdes = Column(
        verbose_name="Reference Designator",
        accessor="inventory__assembly_part__reference_designator__refdes_name",
    )

    def value_coefficient_value_set__notes(self, value):
        notes = []
        for val in value.all():
            if val.notes:
                note = "{}: [{}]".format(val.config_name, val.notes)
                notes.append(note)
        return "\n".join(notes)


class InventoryTestResultTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = InventoryTestResult
        fields = [
            "inventory_test__name",
            "result",
            "inventory__serial_number",
            "inventory__part__name",
            "created_at",
            "user",
            "notes",
            "is_current",
        ]
        base_shown_cols = [
            "inventory_test__name",
            "result",
            "inventory__serial_number",
            "created_at",
            "user",
            "notes",
            "is_current",
        ]

    inventory__serial_number = Column(
        verbose_name="Inventory SN",
        attrs={"style": "white-space: nowrap;"},
        linkify=dict(
            viewname="inventory:inventory_detail", args=[tables.A("inventory__pk")]
        ),
    )
    inventory__part__name = Column(
        verbose_name="Part",
        linkify=dict(
            viewname="parts:parts_detail", args=[tables.A("inventory__part__pk")]
        ),
    )
