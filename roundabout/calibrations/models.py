"""
# Copyright (C) 2019-2020 Woods Hole Oceanographic Institution
#
# This file is part of the Roundabout Database project ("RDB" or 
# "ooicgsn-roundabout").
#
# ooicgsn-roundabout is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# ooicgsn-roundabout is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ooicgsn-roundabout in the COPYING.md file at the project root.
# If not, see <http://www.gnu.org/licenses/>.
"""

from django.db import models
from django.core.validators import MinValueValidator, DecimalValidator, MaxValueValidator, RegexValidator, MaxLengthValidator
from django.utils import timezone
from roundabout.parts.models import Part
from roundabout.inventory.models import Inventory, Deployment, Action
from roundabout.users.models import User
from decimal import Decimal
from sigfig import round
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Tracks Calibration Coefficient event history across Inventory Parts
class CalibrationEvent(models.Model):
    class Meta:
        ordering = ['-calibration_date']
    def __str__(self):
        return self.calibration_date.strftime("%m/%d/%Y")
    def get_object_type(self):
        return 'calibration_event'
    APPROVAL_STATUS = (
        (True, "Approved"),
        (False, "Draft"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    calibration_date = models.DateTimeField(default=timezone.now)
    user_draft = models.ManyToManyField(User, related_name='calibration_events_drafter')
    user_approver = models.ManyToManyField(User, related_name='calibration_events_approver')
    inventory = models.ForeignKey(Inventory, related_name='calibration_events', on_delete=models.CASCADE, null=False)
    deployment = models.ForeignKey(Deployment, related_name='calibration_events', on_delete=models.CASCADE, null=True)
    approved = models.BooleanField(choices=APPROVAL_STATUS, blank=False, default=False)
    detail = models.TextField(blank=True)
    
    def get_actions(self):
        return self.actions.filter(object_type=Action.CALEVENT)


# Tracks Calibrations across Parts
class CoefficientName(models.Model):
    class Meta:
        ordering = ['calibration_name']
        unique_together = ['part','calibration_name']
    def __str__(self):
        return self.calibration_name
    def get_object_type(self):
        return 'coefficient_name'
    VALUE_SET_TYPE = (
        ("sl", "Single"),
        ("1d", "1-Dimensional Array"),
        ("2d", "2-Dimensional Array"),
    )
    calibration_name = models.CharField(max_length=255, unique=False, db_index=True)
    value_set_type = models.CharField(max_length=3, choices=VALUE_SET_TYPE, null=False, blank=False, default="sl")
    sigfig_override = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)], null=False, blank=True, default=3, help_text='Part-based default if sigfigs cannot be captured from input')
    created_at = models.DateTimeField(default=timezone.now)
    part = models.ForeignKey(Part, related_name='coefficient_names', on_delete=models.CASCADE, null=True)

# Tracks Coefficient Sets across Calibrations 
class CoefficientValueSet(models.Model):
    class Meta:
        ordering = ['created_at']
        unique_together = ['calibration_event','coefficient_name']
    def __str__(self):
        return self.value_set
    def get_object_type(self):
        return 'coefficient_value_set'
    value_set = models.TextField(blank=True, help_text='Enter value(s) in either Standard or Scientific Notation (#.##e10, #.##E-12)')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    coefficient_name = models.ForeignKey(CoefficientName, related_name='coefficient_value_sets', on_delete=models.CASCADE, null=True)
    calibration_event = models.ForeignKey(CalibrationEvent, related_name='coefficient_value_sets', on_delete=models.CASCADE, null=True)

# Tracks Coefficeint Values across Coeficient Sets
class CoefficientValue(models.Model):
    class Meta:
        ordering = ['created_at']
    def __str__(self):
        return self.value
    def get_object_type(self):
        return 'coefficient_value'
    NOTATION_FORMAT = (
        ("sci", "Scientific"),
        ("std", "Standard"),
    )
    value = models.CharField(max_length = 21, unique = False, db_index = False)
    original_value = models.CharField(max_length = 21, unique = False, db_index = False, null=True)
    notation_format = models.CharField(max_length=3, choices=NOTATION_FORMAT, null=False, blank=False, default="std")
    sigfig = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(20)], null=False, blank=True, default=3)
    row = models.IntegerField(null=False, blank=True, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    coeff_value_set = models.ForeignKey(CoefficientValueSet, related_name='coefficient_values', on_delete=models.CASCADE, null=True)