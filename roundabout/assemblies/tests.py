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

import datetime

import pytest
from django.test import RequestFactory
from django.utils import timezone

from roundabout.assemblies.forms import AssemblyPartForm
from roundabout.assemblies.models import Assembly, AssemblyPart, AssemblyRevision
from roundabout.assemblies.views import _make_revision_tree_copy, load_part_revisions
from roundabout.parts.models import Part, PartType, Revision

pytestmark = pytest.mark.django_db


@pytest.fixture
def bom_setup(db):
    part_type = PartType.objects.create(name="Instrument")
    part = Part.objects.create(
        name="Widget", part_number="AP-0001", part_type=part_type
    )
    rev_a = Revision.objects.create(
        part=part, revision_code="A",
        created_at=timezone.now() - datetime.timedelta(days=2),
    )
    rev_b = Revision.objects.create(
        part=part, revision_code="B",
        created_at=timezone.now() - datetime.timedelta(days=1),
    )
    other_part = Part.objects.create(
        name="Other", part_number="AP-0002", part_type=part_type
    )
    Revision.objects.create(part=other_part, revision_code="A")

    assembly = Assembly.objects.create(name="Test Assembly")
    assembly_revision = AssemblyRevision.objects.create(
        assembly=assembly, revision_code="A"
    )
    return {
        "part": part,
        "rev_a": rev_a,
        "rev_b": rev_b,
        "other_part": other_part,
        "assembly": assembly,
        "assembly_revision": assembly_revision,
    }


def test_form_revision_field_is_optional_and_scoped_to_part(bom_setup):
    form = AssemblyPartForm(
        data={
            "assembly_revision": bom_setup["assembly_revision"].id,
            "part": bom_setup["part"].id,
            "revision": bom_setup["rev_a"].id,
            "note": "",
        },
        assembly_revision_pk=bom_setup["assembly_revision"].id,
    )
    assert "revision" in form.fields
    assert form.fields["revision"].required is False
    # queryset is scoped to the submitted Part's revisions only
    qs_ids = set(form.fields["revision"].queryset.values_list("id", flat=True))
    assert qs_ids == {bom_setup["rev_a"].id, bom_setup["rev_b"].id}
    assert form.is_valid(), form.errors

    assembly_part = form.save()
    assembly_part.refresh_from_db()
    assert assembly_part.revision == bom_setup["rev_a"]


def test_form_accepts_blank_revision(bom_setup):
    form = AssemblyPartForm(
        data={
            "assembly_revision": bom_setup["assembly_revision"].id,
            "part": bom_setup["part"].id,
            "revision": "",
            "note": "",
        },
        assembly_revision_pk=bom_setup["assembly_revision"].id,
    )
    assert form.is_valid(), form.errors
    assembly_part = form.save()
    assert assembly_part.revision is None


def test_form_rejects_revision_from_a_different_part(bom_setup):
    wrong_revision = Revision.objects.create(
        part=bom_setup["other_part"], revision_code="Z"
    )
    form = AssemblyPartForm(
        data={
            "assembly_revision": bom_setup["assembly_revision"].id,
            "part": bom_setup["part"].id,
            "revision": wrong_revision.id,
            "note": "",
        },
        assembly_revision_pk=bom_setup["assembly_revision"].id,
    )
    assert not form.is_valid()
    assert "revision" in form.errors


def test_load_part_revisions_view(bom_setup):
    request = RequestFactory().get("/", {"part_id": bom_setup["part"].id})
    response = load_part_revisions(request)
    body = response.content.decode("utf-8")
    assert "Any Revision" in body
    assert ">A<" in body and ">B<" in body


def test_revision_tree_copy_carries_pinned_revision(bom_setup):
    ar = bom_setup["assembly_revision"]
    source = AssemblyPart.objects.create(
        assembly_revision=ar,
        part=bom_setup["part"],
        revision=bom_setup["rev_b"],
        order="Widget",
    )
    new_ar = AssemblyRevision.objects.create(
        assembly=bom_setup["assembly"], revision_code="B"
    )

    _make_revision_tree_copy(source, new_ar)

    copied = AssemblyPart.objects.get(assembly_revision=new_ar, part=bom_setup["part"])
    assert copied.revision == bom_setup["rev_b"]


def test_subassembly_cost_prefers_pinned_revision(bom_setup):
    bom_setup["rev_a"].unit_cost = 10
    bom_setup["rev_a"].save()
    bom_setup["rev_b"].unit_cost = 25
    bom_setup["rev_b"].save()

    ap = AssemblyPart.objects.create(
        assembly_revision=bom_setup["assembly_revision"],
        part=bom_setup["part"],
        revision=bom_setup["rev_a"],
        order="Widget",
    )
    assert ap.get_subassembly_total_cost() == 10
