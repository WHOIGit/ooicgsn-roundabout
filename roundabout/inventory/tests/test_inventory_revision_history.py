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


# Tests for Revision change history on a serialized Inventory item: the edit
# form and Bulk Import both log a REVISIONCHANGE Action, which feeds the
# History tab and the "View Field History" popup in Part Specs.

import datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from roundabout.admintools.models import TempImport
from roundabout.inventory.models import Action, Inventory
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(db):
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
    location = Location.objects.create(name="Test Lab", root_type="Land")
    item = Inventory.objects.create(
        serial_number="SN-1", part=part, revision=rev_a, location=location
    )
    return part, rev_a, rev_b, location, item


def test_edit_form_logs_revision_change(client, user, setup):
    part, rev_a, rev_b, location, item = setup
    client.force_login(user)

    response = client.post(
        reverse("inventory:ajax_inventory_update", args=(item.id,)),
        {
            "revision": rev_b.id,
            "serial_number": item.serial_number,
            "old_serial_number": "",
            "hyperlinks-TOTAL_FORMS": 0,
            "hyperlinks-INITIAL_FORMS": 0,
            "hyperlinks-MIN_NUM_FORMS": 0,
            "hyperlinks-MAX_NUM_FORMS": 1000,
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 200, response.content
    item.refresh_from_db()
    assert item.revision == rev_b
    change = item.actions.get(action_type=Action.REVISIONCHANGE)
    assert change.detail == "Revision changed from A to B"
    assert change.user == user


def test_unchanged_revision_logs_nothing(client, user, setup):
    part, rev_a, rev_b, location, item = setup
    client.force_login(user)

    client.post(
        reverse("inventory:ajax_inventory_update", args=(item.id,)),
        {
            "revision": rev_a.id,
            "serial_number": item.serial_number,
            "old_serial_number": "",
            "hyperlinks-TOTAL_FORMS": 0,
            "hyperlinks-INITIAL_FORMS": 0,
            "hyperlinks-MIN_NUM_FORMS": 0,
            "hyperlinks-MAX_NUM_FORMS": 1000,
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert not item.actions.filter(action_type=Action.REVISIONCHANGE).exists()


def test_popup_lists_revision_changes(client, user, setup):
    part, rev_a, rev_b, location, item = setup
    client.force_login(user)
    item.detail = "Revision changed from A to B"
    item.revision = rev_b
    item.save()
    from roundabout.inventory.utils import _create_revision_change_history

    _create_revision_change_history(item, rev_a, rev_b, user)

    html = render_to_string(
        "inventory/modal_inventory_revision_history.html", {"item": item}
    )
    assert "Revision changed from A to B" in html
    assert "Current Revision" in html


def _post_csv(client, body, name, update_existing=False):
    upload = SimpleUploadedFile(name, body.encode("utf-8"), content_type="text/csv")
    data = {"document": upload}
    if update_existing:
        data["update_existing_inventory"] = "on"
    return client.post(reverse("admintools:import_inventory_upload"), data)


def test_full_csv_roundtrip_new_item_gets_csv_revision(client, user, setup):
    part, rev_a, rev_b, location, item = setup
    client.force_login(user)

    body = (
        "Serial Number,Part Number,Revision Code,Location,Notes\r\n"
        "SN-NEW,{pn},A,{loc},\r\n".format(pn=part.part_number, loc=location.name)
    )
    response = _post_csv(client, body, "new.csv")
    assert response.status_code == 302

    tempimport = TempImport.objects.get(name="new.csv")
    cells = {c["field_name"]: c for c in tempimport.tempimportitems.first().data}
    assert cells["Revision Code"]["field_value"] == "A"
    assert cells["Revision Code"]["error"] is False

    preview = client.get(response["Location"])
    assert preview.status_code == 200

    client.get(
        reverse("admintools:import_inventory_upload_add_action", args=(tempimport.id,))
    )
    assert Inventory.objects.get(serial_number="SN-NEW").revision == rev_a


def test_full_csv_roundtrip_existing_item_revision_updated_and_logged(
    client, user, setup
):
    part, rev_a, rev_b, location, item = setup
    client.force_login(user)

    body = (
        "Serial Number,Part Number,Revision Code,Location,Notes\r\n"
        "SN-1,{pn},B,{loc},\r\n".format(pn=part.part_number, loc=location.name)
    )
    response = _post_csv(client, body, "update.csv", update_existing=True)
    tempimport = TempImport.objects.get(name="update.csv")
    client.get(
        reverse("admintools:import_inventory_upload_add_action", args=(tempimport.id,))
    )

    item.refresh_from_db()
    assert item.revision == rev_b
    assert item.actions.filter(action_type=Action.REVISIONCHANGE).count() == 1


def test_revision_code_survives_custom_field_named_revision(client, user, setup):
    # OBSIC has a Custom Field called "Revision"; its (blank) column must not
    # clobber the built-in Revision Code column in the same CSV.
    from roundabout.userdefinedfields.models import Field

    part, rev_a, rev_b, location, item = setup
    Field.objects.create(field_name="Revision", field_type="CharField")
    client.force_login(user)

    body = (
        "Serial Number,Part Number,Revision Code,Location,Notes,Revision\r\n"
        "SN-CF,{pn},A,{loc},,\r\n".format(pn=part.part_number, loc=location.name)
    )
    _post_csv(client, body, "cf.csv")
    tempimport = TempImport.objects.get(name="cf.csv")
    cells = {c["field_name"]: c for c in tempimport.tempimportitems.first().data}
    assert cells["Revision Code"]["field_value"] == "A"

    client.get(
        reverse("admintools:import_inventory_upload_add_action", args=(tempimport.id,))
    )
    assert Inventory.objects.get(serial_number="SN-CF").revision == rev_a
