from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

from roundabout.locations.models import Location
from roundabout.parts.models import Part

# Assembly base model

class Assembly(models.Model):
    name = models.CharField(max_length=255, unique=False, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name
