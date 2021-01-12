from decimal import Decimal
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator, MinLengthValidator

from mptt.models import TreeForeignKey

from roundabout.locations.models import Location

# Cruises app models

class Vessel(models.Model):
    BOOLEAN_CHOICES = (
        (True, 'Yes'), (False, 'No')
    )
    prefix = models.CharField(max_length=10, null=False, blank=True)
    vessel_designation = models.CharField(max_length=10, null=False, blank=True)
    vessel_name = models.CharField(max_length=100)
    ICES_code = models.CharField(null=False, blank=True, max_length=4,
        validators=[MinLengthValidator(4)]
    )
    operator = models.CharField(max_length=100, null=False, blank=True)
    call_sign = models.CharField(max_length=10, null=False, blank=True)
    MMSI_number = models.PositiveIntegerField(null=True, blank=True,
        validators=[MaxValueValidator(999999999), MinValueValidator(100000000)],
        )
    IMO_number = models.PositiveIntegerField(null=True, blank=True,
        validators=[MinValueValidator(1000000), MaxValueValidator(9999999)],
    )
    length = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    max_speed = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    max_draft = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    designation = models.CharField(max_length=10, null=False, blank=True)
    active = models.BooleanField(choices=BOOLEAN_CHOICES, null=True, blank=True)
    R2R = models.BooleanField(choices=BOOLEAN_CHOICES, null=True, blank=True)
    notes = models.TextField(null=False, blank=True)

    class Meta:
        ordering = ('vessel_name',)

    def __str__(self):
        return self.full_vessel_name

    @property
    def full_vessel_name(self):
        return f'{self.vessel_designation} {self.vessel_name}'.strip()


class Cruise(models.Model):
    CUID = models.CharField(max_length=20)
    friendly_name = models.CharField(max_length=100, null=False, blank=True)
    vessel = models.ForeignKey(Vessel, related_name='cruises',
                               on_delete=models.SET_NULL, null=True)
    cruise_start_date = models.DateTimeField()
    cruise_stop_date = models.DateTimeField(null=True)
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
