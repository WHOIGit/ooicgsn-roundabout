import pytest

from django.test import TestCase
from roundabout.admintools.tests.factories import PrinterFactory

pytestmark = pytest.mark.django_db

def test_printer_model():
    """ Test Printer model """
    # create Printer model instance
    printer = PrinterFactory(name="test.whoi.edu")
    assert printer.name == "test.whoi.edu"
    assert printer.__str__() == "test.whoi.edu"
