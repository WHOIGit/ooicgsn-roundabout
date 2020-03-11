from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from roundabout.parts.models import Part
from roundabout.inventory.models import Inventory

from decimal import Decimal

# # Create your models here.
class Calibration(models.Model):
    name = models.CharField(max_length=255, unique=False, db_index=True)
    part = models.ForeignKey(Part, related_name='calibration', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name

    def get_object_type(self):
        return 'calibration'
    

class Coefficient(models.Model):
    value = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], null=False, blank=True, default='0.00')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    inventory = models.ForeignKey(Inventory, related_name='coefficient', on_delete=models.CASCADE, null=True)
    calibration = models.ForeignKey(Calibration, related_name='coefficient', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.value

    def get_object_type(self):
        return 'coefficient'