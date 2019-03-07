import factory

from roundabout.moorings.models import MooringPart
from roundabout.locations.tests.factories import LocationFactory
from roundabout.parts.tests.factories import PartFactory

class MooringPartFactory(factory.DjangoModelFactory):
    """
        Define MooringPart Factory
    """
    class Meta:
        model = MooringPart

    location = factory.SubFactory(LocationFactory)
    part = factory.SubFactory(PartFactory)
    parent = factory.SubFactory('roundabout.moorings.tests.factories.MooringPartFactory')
