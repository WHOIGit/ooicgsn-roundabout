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

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey

from roundabout.userdefinedfields.models import Field


# Create your models here


class PartType(MPTTModel):
    name = models.CharField(max_length=255, unique=False)
    ccc_toggle = models.BooleanField(null=False, default=False)
    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return self.name


class Part(models.Model):
    name = models.CharField(max_length=255, unique=False, db_index=True)
    friendly_name = models.CharField(
        max_length=255, unique=False, null=False, blank=True
    )
    part_type = TreeForeignKey(
        PartType,
        related_name="parts",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        db_index=True,
    )
    part_number = models.CharField(max_length=100, unique=True, db_index=True)
    unit_cost = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        null=False,
        blank=True,
        default="0.00",
    )
    refurbishment_cost = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        null=False,
        blank=True,
        default="0.00",
    )
    note = models.TextField(blank=True)
    custom_fields = models.JSONField(blank=True, null=True)
    user_defined_fields = models.ManyToManyField(
        Field, blank=True, related_name="parts"
    )
    cal_dec_places = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(32)],
        null=False,
        blank=True,
        default=32,
    )
    bulk_upload_event = models.ForeignKey(
        "ooi_ci_tools.BulkUploadEvent",
        related_name="parts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return "parts"

    # get Inventory queryset of all items not in the Trash
    def get_inventory_active(self):
        return self.inventory.exclude(location__root_type="Trash")

    def get_part_inventory_count(self):
        return self.inventory.exclude(location__root_type="Trash").count()

    def get_absolute_url(self):
        return reverse(
            "parts:ajax_parts_detail",
            kwargs={
                "pk": self.pk,
            },
        )

    def friendly_name_display(self):
        if self.friendly_name:
            return self.friendly_name
        else:
            return self.name


class Revision(models.Model):
    revision_code = models.CharField(
        max_length=255, unique=False, db_index=True, default="A"
    )
    unit_cost = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        null=False,
        blank=True,
        default="0.00",
    )
    refurbishment_cost = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        null=False,
        blank=True,
        default="0.00",
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    part = models.ForeignKey(
        Part,
        related_name="revisions",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at", "-revision_code"]
        get_latest_by = "created_at"

    def __str__(self):
        return self.revision_code


class Documentation(models.Model):
    DOC_TYPES = (
        ("Test", "Test Documentation"),
        ("Design", "Design Documentation"),
    )
    name = models.CharField(max_length=255, unique=False)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    doc_link = models.CharField(max_length=1000)
    part = models.ForeignKey(
        Part,
        related_name="documentation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    revision = models.ForeignKey(
        Revision,
        related_name="documentation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["doc_type", "name"]

    def __str__(self):
        return self.name
