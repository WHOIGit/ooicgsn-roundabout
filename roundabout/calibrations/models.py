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

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from roundabout.inventory.models import Inventory, Deployment, Action
from roundabout.parts.models import Part
from roundabout.users.models import User
from roundabout.ooi_ci_tools.models import CCCEvent

# Tracks Calibration Coefficient event history across Inventory Parts
class CalibrationEvent(CCCEvent):
    class Meta:
        ordering = ['-calibration_date']
        get_latest_by = 'calibration_date'
    def __str__(self):
        return self.calibration_date.strftime("%m/%d/%Y")
    def get_object_type(self):
        return 'calibration_event'
    calibration_date = models.DateTimeField(default=timezone.now)

    def get_actions(self):
        return self.actions.filter(object_type=Action.CALEVENT)

    # method to return a date range that corresponds to the period of time when this CalibrationEvent is valid
    # this range corresponds to this calibration_date -> next latest calibration_date.
    # calibration_date is floor of range.
    # Returns a list of datetimes
    def get_valid_calibration_range(self):
        next_event = CalibrationEvent.objects.filter(inventory=self.inventory).filter(calibration_date__gt=self.calibration_date).last()

        if next_event:
            last_date = next_event.calibration_date
        else:
            last_date = timezone.now()

        calibration_range = [self.calibration_date, last_date]
        print(calibration_range)
        print(self)
        return calibration_range

class CalibrationEventHyperlink(models.Model):
    text = models.CharField(max_length=255, unique=False, blank=False, null=False)
    url = models.URLField(max_length=1000)
    parent = models.ForeignKey(CalibrationEvent, related_name='hyperlinks',
                 on_delete=models.CASCADE, null=False, blank=False)

    class Meta: ordering = ['text']
    def __str__(self): return self.text

# Tracks Coefficient Name Event history across Parts
class CoefficientNameEvent(CCCEvent):
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.created_at.strftime("%m/%d/%Y")
    def get_object_type(self):
        return 'coefficient_name_event'

    def get_actions(self):
        return self.actions.filter(object_type='coefficientnameevent')


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
    calibration_name = models.CharField(max_length=255, unique=False, db_index=True, blank=False, null=False)
    value_set_type = models.CharField(max_length=3, choices=VALUE_SET_TYPE, null=False, blank=False, default="sl")
    sigfig_override = models.IntegerField(null=False, blank=True, default=3, help_text='Part-based default if sigfigs cannot be captured from input')
    threshold_low = models.CharField(max_length = 255, unique = False, db_index = False, blank=True, help_text='Coefficient Threshold Low override. (Digits + 1 optional decimal point)')
    threshold_high = models.CharField(max_length = 255, unique = False, db_index = False, blank=True, help_text='Coefficient Threshold High override. (Digits + 1 optional decimal point)')
    deprecated = models.BooleanField(null=False, default=False)
    created_at = models.DateTimeField(default=timezone.now)
    part = models.ForeignKey(Part, related_name='coefficient_names', on_delete=models.CASCADE, null=True)
    coeff_name_event = models.ForeignKey(CoefficientNameEvent, related_name='coefficient_names', on_delete=models.CASCADE, null=True)

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
    def value_set_with_export_formatting(self):
        if self.coefficient_name.value_set_type == '1d':
            return '[{}]'.format(self.value_set)
        elif self.coefficient_name.value_set_type == '2d':
            return 'SheetRef:{}'.format(self.coefficient_name)
        else:  # self.coefficient_name.value_set_type == 'sl'
            return self.value_set

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
    value = models.CharField(max_length = 25, unique = False, db_index = False)
    original_value = models.CharField(max_length = 25, unique = False, db_index = False, null=True)
    notation_format = models.CharField(max_length=3, choices=NOTATION_FORMAT, null=False, blank=False, default="std")
    sigfig = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(20)], null=False, blank=True, default=3)
    row = models.IntegerField(null=False, blank=True, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    coeff_value_set = models.ForeignKey(CoefficientValueSet, related_name='coefficient_values', on_delete=models.CASCADE, null=True)
