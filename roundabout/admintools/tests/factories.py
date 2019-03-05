import factory

from roundabout.admintools.models import Printer


class PrinterFactory(factory.DjangoModelFactory):
    """
        Define Printer Factory
    """
    class Meta:
        model = Printer
