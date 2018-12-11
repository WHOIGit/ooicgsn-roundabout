from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey

# Create your models here.


class Location(MPTTModel):
    LOC_TYPES = (
        ('Array', 'Array'),
        ('Mooring', 'Mooring'),
    )

    name = models.CharField(max_length=100)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True, on_delete=models.SET_NULL)
    location_type = models.CharField(max_length=20, choices=LOC_TYPES, blank=True)
    location_id = models.CharField(max_length=100, blank=True)
    weight = models.IntegerField(default=0, blank=True, null=True)

    class MPTTMeta:
        order_insertion_by = ['weight', 'name']

    def __str__(self):
        return self.name

    def get_mooring_total_cost(self):
        tree = self.mooring_parts.all()
        total_cost = 0
        for item in tree:
            cost = item.part.unit_cost
            total_cost = total_cost + cost

        return total_cost
