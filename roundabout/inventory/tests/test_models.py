import pytest

from django.test import TestCase
from roundabout.inventory.tests.factories import InventoryFactory

pytestmark = pytest.mark.django_db

# Tests
def test_inventory_model():
    """ Test Inventory model """
    # create location model instance
    inventory = InventoryFactory(serial_number="1234-1234-1234-1234")
    assert inventory.serial_number == "1234-1234-1234-1234"
    assert inventory.__str__() ==  "1234-1234-1234-1234"


def test_get_absolute_url_method():
    """ Test get_absolute_url method """
    # create Part  model instance
    inventory = InventoryFactory(serial_number="1234-1234-1234-1234")
    assert inventory.get_absolute_url() == f'/inventory/{inventory.id}/'
