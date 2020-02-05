import pytest

from django.test import TestCase
from roundabout.locations.tests.factories import LocationFactory
from roundabout.parts.tests.factories import PartFactory, RevisionFactory

pytestmark = pytest.mark.django_db

def test_location_model():
    """ Test location model """
    # create location model instance
    location = LocationFactory(name="Test Location")
    assert location.name == "Test Location"
    assert location.__str__() == "Test Location"
