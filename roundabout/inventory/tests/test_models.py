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
