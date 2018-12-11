from django import template
from roundabout.moorings.models import MooringPart
from roundabout.locations.models import Location

register = template.Library()


@register.simple_tag
def get_mooring_parts_by_location(location_pk):
    queryset = MooringPart.objects.filter(location=location_pk).prefetch_related('part__part_type')
    return queryset
