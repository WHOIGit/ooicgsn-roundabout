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

# Tests for the Revision History section (Work Item 2).

import pytest
from django.test import RequestFactory

from roundabout.parts.forms import DocumentationFormset, RevisionForm
from roundabout.parts.models import Revision, RevisionEvent
from roundabout.parts.tests.factories import PartFactory
from roundabout.parts.views import (
    PartsAjaxCreateRevisionView,
    PartsAjaxUpdateRevisionView,
)

pytestmark = pytest.mark.django_db


def _doc_mgmt_form():
    return {
        "documentation-TOTAL_FORMS": "0",
        "documentation-INITIAL_FORMS": "0",
        "documentation-MIN_NUM_FORMS": "0",
        "documentation-MAX_NUM_FORMS": "1000",
    }


def test_log_event_appends_history_row(user):
    part = PartFactory()
    revision = Revision.objects.create(part=part, revision_code="A")

    event = revision.log_event(RevisionEvent.CREATED, user=user, detail="first")

    assert event.revision == revision
    assert event.event_type == RevisionEvent.CREATED
    assert event.user == user
    assert list(revision.revision_events.all()) == [event]


def test_history_is_ordered_oldest_first(user):
    part = PartFactory()
    revision = Revision.objects.create(part=part, revision_code="A")
    first = revision.log_event(RevisionEvent.CREATED, user=user)
    second = revision.log_event(RevisionEvent.UPDATED, user=user)

    assert list(revision.revision_events.all()) == [first, second]


def test_create_revision_view_logs_created_event(user):
    part = PartFactory()
    Revision.objects.create(part=part, revision_code="A")

    data = {
        "revision_code": "B",
        "created_at": "2026-01-01",
        "unit_cost": "0.00",
        "refurbishment_cost": "0.00",
        "note": "",
        "part": part.id,
        **_doc_mgmt_form(),
    }
    request = RequestFactory().post("/", data)
    request.user = user

    view = PartsAjaxCreateRevisionView()
    view.request = request
    view.kwargs = {"part_pk": part.id}
    view.object = None

    form = RevisionForm(data)
    doc_formset = DocumentationFormset(data)
    assert form.is_valid(), form.errors
    assert doc_formset.is_valid(), doc_formset.errors

    view.form_valid(form, doc_formset)

    new_revision = Revision.objects.get(part=part, revision_code="B")
    events = new_revision.revision_events.all()
    assert events.count() == 1
    assert events[0].event_type == RevisionEvent.CREATED
    assert events[0].user == user


def test_update_revision_view_logs_updated_event(user):
    part = PartFactory()
    revision = Revision.objects.create(part=part, revision_code="A")

    data = {
        "revision_code": "A",
        "created_at": "2026-01-02",
        "unit_cost": "1.00",
        "refurbishment_cost": "0.00",
        "note": "changed",
        "part": part.id,
        **_doc_mgmt_form(),
    }
    request = RequestFactory().post("/", data)
    request.user = user

    view = PartsAjaxUpdateRevisionView()
    view.request = request
    view.kwargs = {"pk": revision.id}
    view.object = revision

    form = RevisionForm(data, instance=revision)
    doc_formset = DocumentationFormset(data, instance=revision)
    assert form.is_valid(), form.errors
    assert doc_formset.is_valid(), doc_formset.errors

    view.form_valid(form, doc_formset)

    assert revision.revision_events.filter(
        event_type=RevisionEvent.UPDATED, user=user
    ).exists()
