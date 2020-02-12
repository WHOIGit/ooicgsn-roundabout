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
