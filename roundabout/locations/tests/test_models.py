import pytest

from django.test import TestCase
from roundabout.locations.tests.factories import LocationFactory
from roundabout.moorings.tests.factories import MooringPartFactory
from roundabout.parts.tests.factories import PartFactory, RevisionFactory

pytestmark = pytest.mark.django_db

def test_location_model():
    """ Test location model """
    # create location model instance
    location = LocationFactory(name="Test Location")
    assert location.name == "Test Location"
    assert location.__str__() == "Test Location"

def test_get_mooring_total_cost():
    """ Test get_mooring_total_cost method model """
    part = PartFactory(name="Test Part")
    revision = RevisionFactory(part=part, unit_cost=5.00)
    location = LocationFactory(name="Test Location")
    # create parent MooringPart to be a parent
    parent = MooringPartFactory(parent__parent=None, part=part, location=location)
    mooring = MooringPartFactory(part=part, location=location, parent=parent)
    assert location.get_mooring_total_cost() == 10.00
