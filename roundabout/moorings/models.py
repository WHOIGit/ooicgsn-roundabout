from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey

from roundabout.locations.models import Location
from roundabout.parts.models import Part

# Create your models here.

class MooringPart(MPTTModel):
    part = models.ForeignKey(Part, related_name='mooring_parts',
                          on_delete=models.CASCADE, null=False, blank=False, db_index=True)
    location = TreeForeignKey(Location, related_name='mooring_parts',
                              on_delete=models.CASCADE, null=True, blank=False, db_index=True)
    parent = TreeForeignKey('self', related_name='children',
                            on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    note = models.TextField(blank=True)
    order = models.CharField(max_length=255, null=False, blank=True, db_index=True)

    class MPTTMeta:
        order_insertion_by = ['order']

    def __str__(self):
        return self.part.name

    def get_assembly_total_cost(self):
        tree = self.get_descendants(include_self=True)
        total_cost = 0
        for item in tree:
            revision = item.part.revisions.first()
            cost = revision.unit_cost
            total_cost = total_cost + cost
        return total_cost

    def get_descendants_with_self(self):
        tree = self.get_descendants(include_self=True)
        return tree
