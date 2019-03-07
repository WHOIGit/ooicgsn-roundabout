import factory
from roundabout.locations.models import Location

class LocationFactory(factory.DjangoModelFactory):
    """
        Define Location Factory
    """
    class Meta:
        model = Location
