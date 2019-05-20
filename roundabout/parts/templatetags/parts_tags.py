from django import template
from roundabout.parts.models import Part
from roundabout.locations.models import Location

register = template.Library()


@register.filter
def is_in(var, obj):
    return var in obj

@register.simple_tag
def define(val=None):
    return val

@register.simple_tag
def get_parts_list_by_type(type_pk):
    queryset = Part.objects.filter(part_type=type_pk)
    return queryset

@register.simple_tag
def get_parts_list_by_location(location_pk):
    queryset = Part.objects.filter(location=location_pk).filter(parent=None).prefetch_related('children')
    return queryset

@register.simple_tag
def get_parts_children(pk, location_pk):
    part = Part.objects.get(pk=pk)
    valid_parts = Part.objects.filter(location=location_pk)
    location = Location.objects.get(pk=location_pk)

    def descendants_by_location_tree(part, valid_parts):
        """
        Returns a tree-like structure with progeny for specific Location
        """
        tree = {}
        for f in part.children.all():
            if f in valid_parts:
                tree[f] = descendants_by_location_tree(f, valid_parts)
        return tree

    return descendants_by_location_tree(part, valid_parts)
