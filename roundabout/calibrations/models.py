from django.db import models
from django.core.validators import MinValueValidator, DecimalValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from roundabout.parts.models import Part
from roundabout.inventory.models import Inventory, Deployment
from roundabout.users.models import User
from decimal import Decimal


class CoefficientName(models.Model):
    calibration_name = models.CharField(max_length=255, unique=False, db_index=True)
    part = models.ForeignKey(Part, related_name='coefficient_names', on_delete=models.CASCADE, null=True)
    def __str__(self):
        return self.calibration_name
    def get_object_type(self):
        return 'coefficient_name'
    class Meta:
        ordering = ['calibration_name']


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


class CoefficientValue(models.Model):
    NOTATION_FORMAT = (
        ("sci", "Scientific"),
        ("eng", "Engineering"),
        ("std", "Standard"),
    )
    value = models.CharField(max_length = 20, unique = False, db_index = False)
    notes = models.TextField(blank=True)
    notation_format = models.CharField(max_length=3, choices=NOTATION_FORMAT, null=False, blank=False, default="std")
    created_at = models.DateTimeField(default=timezone.now)
    coefficient_name = models.ForeignKey(CoefficientName, related_name='coefficient_values', on_delete=models.CASCADE, null=True)
    calibration_event = models.ForeignKey(CalibrationEvent, related_name='coefficient_values', on_delete=models.CASCADE, null=True)
    def __str__(self):
        return self.notes
    def get_object_type(self):
        return 'coefficient_value'
