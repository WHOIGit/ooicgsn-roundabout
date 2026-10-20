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

# Tests for Bulk Inventory Import -> Revision wiring (Work Item 3).
# The importer must honour a "Revision" column from the CSV and, when it is
# blank, fall back to the Part's current (newest) Revision instead of silently
# dropping the Revision entirely.

import datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from roundabout.admintools.models import TempImport, TempImportItem
from roundabout.admintools.views import (
    ImportInventoryCreateTemplateView,
    ImportInventoryUploadAddActionView,
)
from roundabout.inventory.models import Inventory
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision

pytestmark = pytest.mark.django_db


def _row(serial, part_number, revision="", location="", notes=""):
    """Build a TempImportItem.data payload the way ImportInventoryUploadView does."""
    return [
        {"field_name": "Serial Number", "field_value": serial, "error": False},
        {"field_name": "Part Number", "field_value": part_number, "error": False},
        {"field_name": "Revision", "field_value": revision, "error": False},
        {"field_name": "Location", "field_value": location, "error": False},
        {"field_name": "Notes", "field_value": notes, "error": False},
    ]


@pytest.fixture
def part_with_revisions(db):
    part_type = PartType.objects.create(name="Instrument")
    part = Part.objects.create(
        name="Widget", part_number="1234-00001-00001", part_type=part_type
    )
    rev_a = Revision.objects.create(
        part=part,
        revision_code="A",
        created_at=timezone.now() - datetime.timedelta(days=2),
    )
    rev_b = Revision.objects.create(
        part=part,
        revision_code="B",
        created_at=timezone.now() - datetime.timedelta(days=1),
    )
    return part, rev_a, rev_b


@pytest.fixture
def lab_location(db):
    return Location.objects.create(name="Test Lab", root_type="Land")


def _run_import(tempimport, user):
    view = ImportInventoryUploadAddActionView()
    request = RequestFactory().get("/")
    request.user = user
    view.request = request
    view.kwargs = {"pk": tempimport.id}
    return view.get_redirect_url()


def test_template_includes_revision_column(user):
    view = ImportInventoryCreateTemplateView()
    request = RequestFactory().get("/")
    request.user = user
    response = view.get(request)
    header_line = response.content.decode("utf-8").splitlines()[0]
    assert "Revision" in header_line.split(",")


def test_blank_revision_falls_back_to_current_revision(
    user, part_with_revisions, lab_location
):
    part, rev_a, rev_b = part_with_revisions
    tempimport = TempImport.objects.create(name="blank.csv", column_headers=[])
    TempImportItem.objects.create(
        tempimport=tempimport,
        data=_row("SN-BLANK", part.part_number, revision="", location=lab_location.name),
    )

    _run_import(tempimport, user)

    item = Inventory.objects.get(serial_number="SN-BLANK")
    # Revision.Meta.ordering => newest first, so the current Revision is "B"
    assert item.revision == rev_b


def test_revision_code_from_csv_is_wired_to_inventory(
    user, part_with_revisions, lab_location
):
    part, rev_a, rev_b = part_with_revisions
    tempimport = TempImport.objects.create(name="rev.csv", column_headers=[])
    TempImportItem.objects.create(
        tempimport=tempimport,
        data=_row("SN-REVA", part.part_number, revision="A", location=lab_location.name),
    )

    _run_import(tempimport, user)

    item = Inventory.objects.get(serial_number="SN-REVA")
    assert item.revision == rev_a


def test_existing_item_revision_moved_when_csv_supplies_code(
    user, part_with_revisions, lab_location
):
    part, rev_a, rev_b = part_with_revisions
    existing = Inventory.objects.create(
        serial_number="SN-EXIST", part=part, revision=rev_a, location=lab_location
    )
    tempimport = TempImport.objects.create(
        name="update.csv", column_headers=[], update_existing_inventory=True
    )
    TempImportItem.objects.create(
        tempimport=tempimport,
        data=_row(
            "SN-EXIST", part.part_number, revision="B", location=lab_location.name
        ),
    )

    _run_import(tempimport, user)

    existing.refresh_from_db()
    assert existing.revision == rev_b


def test_upload_validation_flags_unknown_revision_code(
    client, user, part_with_revisions, lab_location
):
    part, rev_a, rev_b = part_with_revisions
    client.force_login(user)

    csv_body = (
        "Serial Number,Part Number,Revision,Location,Notes\r\n"
        "SN-BAD,{pn},ZZ,{loc},\r\n".format(pn=part.part_number, loc=lab_location.name)
    )
    upload = SimpleUploadedFile(
        "bad_revision.csv", csv_body.encode("utf-8"), content_type="text/csv"
    )

    client.post(
        reverse("admintools:import_inventory_upload"),
        {"document": upload},
    )

    tempimport = TempImport.objects.get(name="bad_revision.csv")
    revision_cells = [
        col
        for item in tempimport.tempimportitems.all()
        for col in item.data
        if col["field_name"] == "Revision"
    ]
    assert revision_cells and revision_cells[0]["error"] is True
