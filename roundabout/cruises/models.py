from django.db import models
from mptt.models import TreeForeignKey

from roundabout.locations.models import Location

# Cruises app models

class Vessel(models.Model):
    BOOLEAN_CHOICES = (
        (True, 'Yes'), (False, 'No')
    )
    prefix = models.CharField(max_length=10, null=False, blank=True)
    vessel_designation = models.CharField(max_length=10, default="R/V")
    vessel_name = models.CharField(max_length=100)
    ICES_code = models.CharField(max_length=10, null=False, blank=True)
    operator = models.CharField(max_length=100, null=False, blank=True)
    call_sign = models.CharField(max_length=10, null=False, blank=True)
    MMSI_number = models.IntegerField(null=True, blank=True)
    IMO_number = models.IntegerField(null=True, blank=True)
    length = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    max_speed = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    max_draft = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    designation = models.CharField(max_length=10, null=False, blank=True)
    active = models.BooleanField(choices=BOOLEAN_CHOICES, null=True, default=True)
    R2R = models.BooleanField(choices=BOOLEAN_CHOICES, null=True, default=True, blank=True)
    notes = models.TextField(null=False, blank=True)


    class Meta:
        ordering = ('vessel_name',)

    def __str__(self):
        return '%s %s' % (self.vessel_designation, self.vessel_name)


class Cruise(models.Model):
    CUID = models.CharField(max_length=20)
    friendly_name = models.CharField(max_length=100, null=False, blank=True)
    vessel = models.ForeignKey(Vessel, related_name='cruises',
                               on_delete=models.SET_NULL, null=True)
    cruise_start_date = models.DateTimeField()
    cruise_stop_date = models.DateTimeField()
    notes = models.TextField(null=False, blank=True)
    location = TreeForeignKey(Location, related_name='cruises', verbose_name='Destination',
                              on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ('-cruise_start_date',)

    def __str__(self):
        return self.CUID

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return 'cruises'
