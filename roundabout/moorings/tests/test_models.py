import pytest

from django.test import TestCase
from roundabout.moorings.tests.factories import MooringPartFactory
from roundabout.parts.tests.factories import PartFactory, RevisionFactory
from roundabout.locations.tests.factories import LocationFactory

pytestmark = pytest.mark.django_db

def test_mooringpart_model():
    """ Test MooringPart model """
    # create model instances
    part = PartFactory(name="Test Part")
    location = LocationFactory(name="Test Location")
    # create parent MooringPart to test self foreign key
    parent = MooringPartFactory(parent__parent=None, part=part, location=location)
    mooring = MooringPartFactory(part=part, location=location, parent=parent)

    assert mooring.part == part
    assert mooring.location == location
    assert mooring.parent == parent
    assert mooring.__str__() == part.name


def test_get_assembly_total_cost_method():
    """ Test get_assembly_total_cost method """
    # create model instances
    part1 = PartFactory(name="Test Part", )
    revision1 = RevisionFactory(part=part1, unit_cost=5.00)
    part2 = PartFactory(name="Test Part", )
    revision2 = RevisionFactory(part=part2, unit_cost=10.00)
    location = LocationFactory(name="Test Location")

    parent1 = MooringPartFactory(parent__parent=None, part=part1, location=location)
    mooring = MooringPartFactory(parent=parent1, part=part2, location=location)

    # Does the total cost equal number of assembly items?
    assert parent1.get_assembly_total_cost() == 15.00


def test_get_descendants_with_self_method():
    """ Test get_descendants_with_self method """
    # create model instances
    part = PartFactory(name="Test Part")
    location = LocationFactory(name="Test Location")

    parent1 = MooringPartFactory(parent__parent=None, part=part, location=location)
    mooring = MooringPartFactory(parent=parent1, part=part, location=location)

    # Is the parent item in the TreeQueryset?
    assert parent1 in parent1.get_descendants_with_self()
