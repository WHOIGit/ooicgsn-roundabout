import pytest

from django.test import TestCase
from roundabout.parts.tests.factories import PartFactory, PartTypeFactory, DocumentationFactory
from roundabout.inventory.tests.factories import InventoryFactory

pytestmark = pytest.mark.django_db

def test_part_model():
    """ Test Part model """
    # create Part and PartType model instance
    part_type = PartTypeFactory(name="Test Part Type")
    part = PartFactory(name="Test Part", part_type=part_type)

    assert part.name == "Test Part"
    assert part.part_type == part_type
    assert part.__str__() == "Test Part"


def test_get_part_inventory_count_method():
    """ Test get_part_inventory_count method """
    # create Part model instance
    part = PartFactory(name="Test Part")
    inventory1 = InventoryFactory(part=part)
    inventory2 = InventoryFactory(part=part)
    # Total count of inventory items of same Part object
    assert part.get_part_inventory_count() == 2


def test_get_absolute_url_method():
    """ Test get_absolute_url method """
    # create Part  model instance
    part = PartFactory(name="Test Part")
    assert part.get_absolute_url() == f'/parts/{part.id}/'
