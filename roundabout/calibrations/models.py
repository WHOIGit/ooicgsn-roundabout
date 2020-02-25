from django.db import models
from django.core.validators import MinValueValidator

from decimal import Decimal

# # Create your models here.
class Calibration(models.Model):
    name = models.CharField(max_length=255, unique=False, db_index=True)
    coefficient = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], null=False, blank=True, default='0.00')

    def __str__(self):
        return self.name

    def get_object_type(self):
        return 'calibration'
    
    