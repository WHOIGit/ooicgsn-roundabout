# Tests for the backfill_null_revisions management command.

from io import StringIO

import pytest
from django.core.management import call_command

from roundabout.inventory.models import Inventory
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision

pytestmark = pytest.mark.django_db


@pytest.fixture
def data(db):
    part_type = PartType.objects.create(name="Instrument")
    location = Location.objects.create(name="Lab", root_type="Land")

    # Part with exactly one Rev A: blanks should be filled.
    good = Part.objects.create(name="Good", part_number="G-1", part_type=part_type)
    good_a = Revision.objects.create(part=good, revision_code="A")
    Revision.objects.create(part=good, revision_code="B")

    # Part with no Rev A: blanks are skipped.
    no_a = Part.objects.create(name="NoA", part_number="N-1", part_type=part_type)
    Revision.objects.create(part=no_a, revision_code="B")

    # Part with duplicate Rev A: blanks are skipped.
    dup = Part.objects.create(name="Dup", part_number="D-1", part_type=part_type)
    Revision.objects.create(part=dup, revision_code="A")
    Revision.objects.create(part=dup, revision_code="A")

    def make(serial, part, revision=None):
        return Inventory.objects.create(
            serial_number=serial, part=part, revision=revision, location=location
        )

    return {
        "good_a": good_a,
        "blank": make("GOOD-BLANK", good),
        "already_b": make("GOOD-B", good, good.revisions.get(revision_code="B")),
        "no_a": make("NOA-BLANK", no_a),
        "dup": make("DUP-BLANK", dup),
    }


def run(*args):
    out = StringIO()
    call_command("backfill_null_revisions", *args, stdout=out)
    return out.getvalue()


def test_dry_run_writes_nothing(data):
    output = run()
    assert "Would update 1 item(s)" in output
    assert "Dry run only" in output
    data["blank"].refresh_from_db()
    assert data["blank"].revision is None


def test_apply_fills_only_unambiguous_blanks(data):
    output = run("--apply")
    assert "Updated 1 item(s)" in output
    assert "Skipped 2" in output
    assert "NOA-BLANK" in output and "DUP-BLANK" in output

    data["blank"].refresh_from_db()
    assert data["blank"].revision == data["good_a"]
    # Skipped items stay blank.
    for key in ("no_a", "dup"):
        data[key].refresh_from_db()
        assert data[key].revision is None
    # Items with an existing revision are untouched.
    data["already_b"].refresh_from_db()
    assert data["already_b"].revision.revision_code == "B"


def test_apply_is_idempotent(data):
    run("--apply")
    assert "Updated 0 item(s)" in run("--apply")
