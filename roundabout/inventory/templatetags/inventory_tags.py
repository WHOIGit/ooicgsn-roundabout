from django import template
from roundabout.inventory.models import Inventory, Action, Deployment
from roundabout.locations.models import Location
from roundabout.parts.models import Part
from roundabout.moorings.models import MooringPart

register = template.Library()


@register.simple_tag
def get_mooringpart_list_by_deployment(dep_pk):
    deployment = Deployment.objects.select_related('final_location').get(id=dep_pk)
    queryset = MooringPart.objects.filter(location=deployment.final_location).prefetch_related('part').prefetch_related('part__part_type')
    return queryset


@register.simple_tag
def get_inventory_dictionary(inventory_qs):
    inventory_dict = {}
    for i in inventory_qs.all():
        inventory_dict[i.mooring_part_id] = i.id
    return inventory_dict


@register.simple_tag
def get_inventory_destination_dictionary(assigned_destination_root):
    inventory_dict = {}
    inventory_qs = Inventory.objects.filter(assigned_destination_root=assigned_destination_root)
    for i in inventory_qs.all():
        inventory_dict[i.mooring_part_id] = i.id
    return inventory_dict


@register.simple_tag
def get_inventory_queryset_by_deployment(dep_pk):
    queryset = Inventory.objects.filter(deployment_id=dep_pk)
    return queryset


@register.simple_tag
def get_inventory_list_by_location(location):
    if location.deployment.exists():
        queryset = location.inventory.filter(deployment__isnull=True).filter(mooring_part__isnull=True).prefetch_related('part__part_type')
    else:
        queryset = location.inventory.filter(mooring_part__isnull=True).prefetch_related('part__part_type')
    return queryset


@register.simple_tag
def get_inventory_snapshot_list_by_location(location, dep):
    if location.deployment_snapshot.exists():
        queryset = location.inventory_snapshot.filter(deployment=dep).prefetch_related('inventory__part__part_type')
    else:
        queryset = location.inventory_snapshot.filter(deployment=dep).prefetch_related('inventory__part__part_type')
    return queryset


@register.simple_tag
def get_inventory_list_by_location_with_destination(location):
    queryset = location.inventory.filter(mooring_part__isnull=False).filter(deployment__isnull=True).filter(assigned_destination_root__isnull=False).prefetch_related('part__part_type')
    return queryset


@register.simple_tag
def get_locations_by_mooring(location_pk):
    queryset = Location.objects.filter(parent_id=location_pk)
    queryset = Location.objects.get_queryset_descendants(
        queryset, include_self=True).prefetch_related('inventory')
    return queryset


@register.simple_tag
def get_part_by_inventory(part_pk):
    queryset = Part.objects.get(id=part_pk).get_family()
    return queryset

# Custom filter to get dictionary values by key

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

# Custom tag for diagnostics

@register.simple_tag
def debug_object_dump(var):
    return vars(var)
