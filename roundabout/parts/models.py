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

class PartType(MPTTModel):
    PART_TYPES = (
        ('Cable', 'Cable'),
        ('Electrical', 'Electrical'),
        ('Mechanical', 'Mechanical'),
        ('Sensor', 'Sensor'),
    )
    name = models.CharField(max_length=255, unique=False)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.SET_NULL)

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class Part(models.Model):
    PART_TYPES = (
        ('Cable', 'Cable'),
        ('Electrical', 'Electrical'),
        ('Mechanical', 'Mechanical'),
        ('Sensor', 'Sensor'),
    )
    name = models.CharField(max_length=255, unique=False, db_index=True)
    friendly_name = models.CharField(max_length=255, unique=False, null=False, blank=True)
    part_type = TreeForeignKey(PartType, related_name='parts', on_delete=models.SET_NULL, null=True, blank=False, db_index=True)
    revision = models.CharField(max_length=100, blank=True)
    part_number = models.CharField(max_length=100, unique=False, db_index=True)
    unit_cost = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], null=False, blank=True, default='0.00')
    refurbishment_cost = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], null=False, blank=True, default='0.00')
    note = models.TextField(blank=True)
    custom_fields = JSONField(blank=True, null=True)
    user_defined_fields = models.ManyToManyField(Field, blank=True, related_name='parts')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return 'parts'

    def get_part_inventory_count(self):
        return self.inventory.count()

    def get_absolute_url(self):
        return reverse('parts:ajax_parts_detail', kwargs={'pk': self.pk, })

    def friendly_name_display(self):
        if self.friendly_name:
            return self.friendly_name
        else:
            return self.name

    def csv_row(self,headers):
        #TODO
        # rn this is not being searched for....
        #TODO ALSO search in UDF field DEFAULTS for certain parts. eg. model:motorola is a default for many telemetry part templates udf.
        return []


class Revision(models.Model):
    revision_code = models.CharField(max_length=255, unique=False, db_index=True, default='A')
    unit_cost = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], null=False, blank=True, default='0.00')
    refurbishment_cost = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], null=False, blank=True, default='0.00')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    part = models.ForeignKey(Part, related_name='revisions',
                          on_delete=models.CASCADE, null=False, blank=False, db_index=True)

    class Meta:
        ordering = ['-created_at', '-revision_code']

    def __str__(self):
        return self.revision_code


class Documentation(models.Model):
    DOC_TYPES = (
        ('Test', 'Test Documentation'),
        ('Design', 'Design Documentation'),
    )
    name = models.CharField(max_length=255, unique=False)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    doc_link = models.CharField(max_length=1000)
    part = models.ForeignKey(Part, related_name='documentation',
                             on_delete=models.CASCADE, null=True, blank=True)
    revision = models.ForeignKey(Revision, related_name='documentation',
                             on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['doc_type', 'name']

    def __str__(self):
        return self.name
