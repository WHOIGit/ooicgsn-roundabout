import factory
from random import randint

from roundabout.inventory.models import Inventory, Deployment
from roundabout.moorings.models import MooringPart
from roundabout.locations.tests.factories import LocationFactory
from roundabout.parts.tests.factories import PartFactory

# Generate random Part Numbers in the correct format
def generate_serial_number():
    return str( randint(1000, 9999) ) + '-' + str( randint(1000, 9999) ) +  \
            '-' + str( randint(1000, 9999) ) + '-' + str( randint(1000, 9999) )


# Factories
class DeploymentFactory(factory.DjangoModelFactory):
    """
        Define Deployment Factory
    """
    class Meta:
        model = Deployment


class InventoryFactory(factory.DjangoModelFactory):
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
