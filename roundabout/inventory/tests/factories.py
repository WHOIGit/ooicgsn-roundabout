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

import factory
from factory.django import DjangoModelFactory
from random import randint

from roundabout.inventory.models import Inventory, Deployment
from roundabout.locations.tests.factories import LocationFactory
from roundabout.parts.tests.factories import PartFactory

# Generate random Part Numbers in the correct format
def generate_serial_number():
    return str( randint(1000, 9999) ) + '-' + str( randint(1000, 9999) ) +  \
            '-' + str( randint(1000, 9999) ) + '-' + str( randint(1000, 9999) )


# Factories
class DeploymentFactory(DjangoModelFactory):
    """
        Define Deployment Factory
    """
    class Meta:
        model = Deployment


class InventoryFactory(DjangoModelFactory):
    """
        Define Inventory Factory
    """
    serial_number = factory.LazyFunction(generate_serial_number)

    class Meta:
        model = Inventory
        django_get_or_create = ('serial_number',)

    location = factory.SubFactory(LocationFactory)
    part = factory.SubFactory(PartFactory)
    #parent = factory.SubFactory('roundabout.inventory.tests.factories.InventoryFactory')
