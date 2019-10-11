from decimal import Decimal
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator
from mptt.models import MPTTModel, TreeForeignKey

from roundabout.locations.models import Location
from roundabout.userdefinedfields.models import Field

# Create your models here

"""
class Report or ReportTemplate(models.Model):

    name = models.CharField(max_length=255, unique=False, db_index=True)
    model = 

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return 'reports'
"""
