import factory
import random, string

from roundabout.parts.models import Part, PartType, Documentation, Revision

from faker import Faker
fake = Faker()

# Generate random Part Numbers in the correct format
def generate_part_number():
    return random.choice(string.digits) + '-' + random.choice(string.digits)


# Factories
class PartTypeFactory(factory.DjangoModelFactory):
    """
        Define Part Type Factory
    """
    class Meta:
        model = PartType


class PartFactory(factory.DjangoModelFactory):
    """
        Define Part Factory
    """
    part_number = factory.LazyFunction(generate_part_number)

    class Meta:
        model = Part
        django_get_or_create = ('part_number',)

    part_type = factory.SubFactory(PartTypeFactory)


class RevisionFactory(factory.DjangoModelFactory):
    """
        Define Revision Factory
    """
    class Meta:
        model = Revision

    part = factory.SubFactory(Part)


class DocumentationFactory(factory.DjangoModelFactory):
    """
        Define Documentatione Factory
    """
    class Meta:
        model = Documentation

    part = factory.SubFactory(Part)
