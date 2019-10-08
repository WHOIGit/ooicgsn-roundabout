from django import template
import datetime

from roundabout.inventory.models import Inventory, Action, Deployment
from roundabout.locations.models import Location
from roundabout.parts.models import Part
from roundabout.userdefinedfields.models import Field, FieldValue

register = template.Library()

# Return tomorrow's date for Deployment maxDate validation
@register.simple_tag
def tomorrow(format):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    return tomorrow.strftime(format)
