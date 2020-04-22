from django.db import models

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

    class Meta:
        ordering = ('vessel_name',)

    def __str__(self):
        return self.vessel_name
