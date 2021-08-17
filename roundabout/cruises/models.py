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

from decimal import Decimal
from django.db import models
from django.apps import apps
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    MinLengthValidator,
)
from mptt.models import TreeForeignKey

# Cruises app models


class Vessel(models.Model):
    BOOLEAN_CHOICES = ((True, "Yes"), (False, "No"))
    prefix = models.CharField(max_length=10, null=False, blank=True)
    vessel_designation = models.CharField(max_length=10, null=False, blank=True)
    vessel_name = models.CharField(max_length=100)
    ICES_code = models.CharField(
        null=False, blank=True, max_length=4, validators=[MinLengthValidator(4)]
    )
    operator = models.CharField(max_length=100, null=False, blank=True)
    call_sign = models.CharField(max_length=10, null=False, blank=True)
    MMSI_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(999999999), MinValueValidator(100000000)],
    )
    IMO_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1000000), MaxValueValidator(9999999)],
    )
    length = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    max_speed = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    max_draft = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    designation = models.CharField(max_length=10, null=False, blank=True)
    active = models.BooleanField(choices=BOOLEAN_CHOICES, null=True, blank=True)
    R2R = models.BooleanField(choices=BOOLEAN_CHOICES, null=True, blank=True)
    notes = models.TextField(null=False, blank=True)

    class Meta:
        ordering = ("vessel_name",)

    def __str__(self):
        return self.full_vessel_name

    @property
    def full_vessel_name(self):
        return f"{self.vessel_designation} {self.vessel_name}".strip()

    def get_actions(self):
        return self.actions.filter(object_type=apps.get_model('inventory.Action').VESSEL)

class VesselHyperlink(models.Model):
    text = models.CharField(max_length=255, unique=False)
    url = models.URLField(max_length=1000)
    parent = models.ForeignKey(
        Vessel,
        related_name="hyperlinks",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )

    class Meta:
        ordering = ["text"]

    def __str__(self):
        return self.text


class Cruise(models.Model):
    CUID = models.CharField(max_length=20, unique=True)
    friendly_name = models.CharField(max_length=100, null=False, blank=True)
    vessel = models.ForeignKey(
        Vessel, related_name="cruises", on_delete=models.SET_NULL, null=True
    )
    cruise_start_date = models.DateTimeField()
    cruise_stop_date = models.DateTimeField(null=True)
    notes = models.TextField(null=False, blank=True)
    location = TreeForeignKey(
        "locations.Location",
        related_name="cruises",
        verbose_name="Destination",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-cruise_start_date",)

    def __str__(self):
        return self.CUID

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return "cruises"

    def get_actions(self):
        return self.actions.filter(object_type=apps.get_model('inventory.Action').CRUISE)

class CruiseHyperlink(models.Model):
    text = models.CharField(max_length=255, unique=False)
    url = models.URLField(max_length=1000)
    parent = models.ForeignKey(
        Cruise,
        related_name="hyperlinks",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )

    class Meta:
        ordering = ["text"]

    def __str__(self):
        return self.text
