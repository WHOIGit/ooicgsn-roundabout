from django.db import models
from mptt.models import TreeForeignKey
from django.utils import timezone

from roundabout.locations.models import Location
from roundabout.assemblies.models import Assembly

# Build model

class Build(models.Model):
    build_number = models.CharField(max_length=255, unique=False)
    location = TreeForeignKey(Location, related_name='builds',
                              on_delete=models.SET_NULL, null=True, blank=False)
    assembly = models.ForeignKey(Assembly, related_name='builds',
                             on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['assembly', 'build_number']

    def __str__(self):
        return '%s - %s' % (self.build_number, self.assembly.name)
