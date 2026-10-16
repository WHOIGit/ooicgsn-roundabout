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

# Tests for the Part / Revision -> Assemblies reverse lookup (Work Item 5).

import pytest

from roundabout.assemblies.models import Assembly, AssemblyPart, AssemblyRevision
from roundabout.parts.models import Part, PartType, Revision

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(db):
    part_type = PartType.objects.create(name="Instrument")
    part = Part.objects.create(name="Widget", part_number="RL-1", part_type=part_type)
    rev_a = Revision.objects.create(part=part, revision_code="A")
    rev_b = Revision.objects.create(part=part, revision_code="B")

    assembly = Assembly.objects.create(name="Mooring")
    ar1 = AssemblyRevision.objects.create(assembly=assembly, revision_code="A")
    ar2 = AssemblyRevision.objects.create(assembly=assembly, revision_code="B")

    # ar1 pins Revision A; ar2 uses the Part with no pinned Revision
    AssemblyPart.objects.create(
        assembly_revision=ar1, part=part, revision=rev_a, order="w"
    )
    AssemblyPart.objects.create(
        assembly_revision=ar2, part=part, revision=None, order="w"
    )
    return part, rev_a, rev_b, ar1, ar2


def test_revision_reverse_lookup_is_revision_scoped(setup):
    part, rev_a, rev_b, ar1, ar2 = setup

    assert list(rev_a.get_assembly_revisions_used_in()) == [ar1]
    assert list(rev_b.get_assembly_revisions_used_in()) == []


def test_part_reverse_lookup_covers_all_bom_slots(setup):
    part, rev_a, rev_b, ar1, ar2 = setup

    found = set(part.get_assembly_revisions_used_in().values_list("id", flat=True))
    assert found == {ar1.id, ar2.id}


def test_part_reverse_lookup_is_distinct(setup):
    part, rev_a, rev_b, ar1, ar2 = setup
    # a second slot for the same Part in the same Assembly Revision
    AssemblyPart.objects.create(
        assembly_revision=ar1, part=part, revision=rev_a, order="w2"
    )

    assert part.get_assembly_revisions_used_in().count() == 2
