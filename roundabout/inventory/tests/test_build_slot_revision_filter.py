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

# Tests for Item 6: filtering available Inventory for a Build slot by the
# Part Revision pinned on that slot (AssemblyPart.revision).

import pytest
from django.test import RequestFactory

from roundabout.assemblies.models import Assembly, AssemblyPart, AssemblyRevision
from roundabout.builds.models import Build
from roundabout.inventory.models import Inventory
from roundabout.inventory.views import InventoryAjaxByAssemblyPartListView
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision

pytestmark = pytest.mark.django_db


@pytest.fixture
def slot_setup(db):
    part_type = PartType.objects.create(name="Instrument")
    part = Part.objects.create(name="Widget", part_number="B6-1", part_type=part_type)
    rev_a = Revision.objects.create(part=part, revision_code="A")
    rev_b = Revision.objects.create(part=part, revision_code="B")

    location = Location.objects.create(name="Lab", root_type="Land")
    assembly = Assembly.objects.create(name="Mooring")
    assembly_revision = AssemblyRevision.objects.create(
        assembly=assembly, revision_code="A"
    )
    build = Build.objects.create(
        build_number="00001",
        assembly=assembly,
        assembly_revision=assembly_revision,
        location=location,
    )

    item_a = Inventory.objects.create(
        serial_number="ITEM-A", part=part, revision=rev_a, location=location
    )
    item_b = Inventory.objects.create(
        serial_number="ITEM-B", part=part, revision=rev_b, location=location
    )
    item_none = Inventory.objects.create(
        serial_number="ITEM-NONE", part=part, revision=None, location=location
    )
    return {
        "part": part,
        "rev_a": rev_a,
        "rev_b": rev_b,
        "location": location,
        "assembly_revision": assembly_revision,
        "build": build,
        "item_a": item_a,
        "item_b": item_b,
        "item_none": item_none,
    }


def _available_items(assembly_part, slot_setup):
    view = InventoryAjaxByAssemblyPartListView()
    view.request = RequestFactory().get("/")
    view.kwargs = {
        "pk": assembly_part.id,
        "location_pk": slot_setup["location"].id,
        "build_pk": slot_setup["build"].id,
    }
    context = view.get_context_data()
    return set(context["inventory_items"].values_list("serial_number", flat=True))


def test_pinned_slot_shows_only_matching_revision(slot_setup):
    assembly_part = AssemblyPart.objects.create(
        assembly_revision=slot_setup["assembly_revision"],
        part=slot_setup["part"],
        revision=slot_setup["rev_a"],
        order="w",
    )
    assert _available_items(assembly_part, slot_setup) == {"ITEM-A"}


def test_unpinned_slot_hides_nothing(slot_setup):
    assembly_part = AssemblyPart.objects.create(
        assembly_revision=slot_setup["assembly_revision"],
        part=slot_setup["part"],
        revision=None,
        order="w",
    )
    assert _available_items(assembly_part, slot_setup) == {
        "ITEM-A",
        "ITEM-B",
        "ITEM-NONE",
    }


def test_accepts_inventory_revision_helper(slot_setup):
    pinned = AssemblyPart.objects.create(
        assembly_revision=slot_setup["assembly_revision"],
        part=slot_setup["part"],
        revision=slot_setup["rev_a"],
        order="w",
    )
    legacy = AssemblyPart.objects.create(
        assembly_revision=slot_setup["assembly_revision"],
        part=slot_setup["part"],
        revision=None,
        order="w2",
    )
    assert pinned.accepts_inventory_revision(slot_setup["item_a"]) is True
    assert pinned.accepts_inventory_revision(slot_setup["item_b"]) is False
    assert pinned.accepts_inventory_revision(slot_setup["item_none"]) is False
    assert legacy.accepts_inventory_revision(slot_setup["item_b"]) is True
