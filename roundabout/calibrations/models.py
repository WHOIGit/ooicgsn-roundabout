from django.db import models
from django.core.validators import MinValueValidator, DecimalValidator, MaxValueValidator, RegexValidator, MaxLengthValidator
from django.utils import timezone
from roundabout.parts.models import Part
from roundabout.inventory.models import Inventory, Deployment
from roundabout.users.models import User
from decimal import Decimal
from sigfig import round
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Tracks Calibrations across Parts
class CoefficientName(models.Model):
    VALUE_SET_TYPE = (
        ("sl", "Single"),
        ("1d", "1-Dimensional Array"),
        ("2d", "2-DImensional Array"),
    )
    calibration_name = models.CharField(max_length=255, unique=False, db_index=True)
    value_set_type = models.CharField(max_length=3, choices=VALUE_SET_TYPE, null=False, blank=False, default="sl")
    sigfig_override = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)], null=False, blank=True, default=3)
    part = models.ForeignKey(Part, related_name='coefficient_names', on_delete=models.CASCADE, null=True)
    def __str__(self):
        return self.calibration_name
    def get_object_type(self):
        return 'coefficient_name'
    class Meta:
        ordering = ['calibration_name']

# Tracks Calibration Coefficient event history across Inventory items
class CalibrationEvent(models.Model):
    APPROVAL_STATUS = (
        (True, "Approved"),
        (False, "Draft"),
    )
    created_at = models.DateTimeField(default=timezone.now)
    calibration_date = models.DateTimeField(default=timezone.now)
    user_draft = models.ForeignKey(User, related_name='calibration_events_drafter', on_delete=models.SET_NULL, null=True, blank=False)
    user_approver = models.ForeignKey(User, related_name='calibration_events_approver', on_delete=models.SET_NULL, null=True, blank=False)
    inventory = models.ForeignKey(Inventory, related_name='calibration_events', on_delete=models.CASCADE, null=False)
    deployment = models.ForeignKey(Deployment, related_name='calibration_events', on_delete=models.CASCADE, null=True)
    approved = models.BooleanField(choices=APPROVAL_STATUS, blank=False, default=False)
    def __str__(self):
        return self.calibration_date
    def get_object_type(self):
        return 'calibration_event'
    class Meta:
        ordering = ['-calibration_date']

# Tracks Coefficients across Calibrations 
class CoefficientValue(models.Model):
    VALUE_SET_TYPE = (
        ("sl", "Single"),
        ("1d", "1-Dimensional Array"),
        ("2d", "2-DImensional Array"),
    )
    NOTATION_FORMAT = (
        ("sci", "Scientific"),
        ("eng", "Engineering"),
        ("std", "Standard"),
    )
    value_set = models.TextField(blank=True)
    value_set_type = models.CharField(max_length=3, choices=VALUE_SET_TYPE, null=False, blank=True, default="sl")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    coefficient_name = models.ForeignKey(CoefficientName, related_name='coefficient_value_sets', on_delete=models.CASCADE, null=True)
    calibration_event = models.ForeignKey(CalibrationEvent, related_name='coefficient_value_sets', on_delete=models.CASCADE, null=True)
    value = models.CharField(max_length = 21, unique = False, db_index = False)
    notation_format = models.CharField(max_length=3, choices=NOTATION_FORMAT, null=False, blank=False, default="std")
    def __str__(self):
        return self.value_set
    def get_object_type(self):
        return 'coefficient_value_set'
    class Meta:
        ordering = ['created_at']
        unique_together = ['calibration_event','coefficient_name']