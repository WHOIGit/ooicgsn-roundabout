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
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey
from model_utils import FieldTracker

from roundabout.parts.models import Part

# Assembly Types model
class AssemblyType(models.Model):
    name = models.CharField(max_length=255, unique=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# Assembly base model
class Assembly(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    assembly_type = models.ForeignKey(
        AssemblyType,
        related_name="assemblies",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    assembly_number = models.CharField(
        max_length=100, unique=False, db_index=True, null=False, blank=True
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = [
            "name",
        ]

    def __str__(self):
        return self.name

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return "assemblies"

    def has_nontrashed_nonretired_builds(self):
        for build in self.builds.all():
            if build.location.get_root().root_type == 'Retired': continue
            if build.location.get_root().root_type == 'Trash': continue
            return True

class AssemblyRevision(models.Model):
    revision_code = models.CharField(
        max_length=255, unique=False, db_index=True, default="A"
    )
    revision_note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Release Date")
    assembly = models.ForeignKey(
        Assembly,
        related_name="assembly_revisions",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_index=True,
    )

    class Meta:
        ordering = ["-id", "-revision_code"]
        get_latest_by = "created_at"

    def __str__(self):
        return "Revision %s - %s" % (self.revision_code, self.assembly.name)

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return "assemblyrevisions"

    def get_assembly_total_cost(self):
        tree = self.assembly_parts.all()
        total_cost = 0

        for item in tree:
            revision = item.part.revisions.first()
            cost = revision.unit_cost
            total_cost = total_cost + cost

        return total_cost


# Assembly documentation model
class AssemblyDocument(models.Model):
    DOC_TYPES = (
        ("Test", "Test Documentation"),
        ("Design", "Design Documentation"),
    )
    name = models.CharField(max_length=255, unique=False)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    doc_link = models.URLField(max_length=1000)
    assembly_revision = models.ForeignKey(
        AssemblyRevision,
        related_name="assembly_documents",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["doc_type", "name"]

    def __str__(self):
        return self.name


# Assembly parts model
class AssemblyPart(MPTTModel):
    assembly = models.ForeignKey(
        Assembly,
        related_name="assembly_parts",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
    )
    assembly_revision = models.ForeignKey(
        AssemblyRevision,
        related_name="assembly_parts",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
    )
    part = models.ForeignKey(
        Part,
        related_name="assembly_parts",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_index=True,
    )
    parent = TreeForeignKey(
        "self",
        related_name="children",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
    )
    reference_designator = models.ForeignKey(
        'ooi_ci_tools.ReferenceDesignator',
        related_name="assembly_parts",
        on_delete=models.SET_NULL,
        null=True
    )
    note = models.TextField(blank=True)
    order = models.CharField(max_length=255, null=False, blank=True, db_index=True)
    ci_deployedBy = models.CharField(
        max_length=255, unique=False, db_index=False, blank=True
    )
    ci_recoveredBy = models.CharField(
        max_length=255, unique=False, db_index=False, blank=True
    )
    ci_versionNumber = models.CharField(
        max_length=255, unique=False, db_index=False, blank=True
    )
    ci_orbit = models.CharField(
        max_length=255, unique=False, db_index=False, blank=True
    )
    ci_deployment_depth = models.CharField(
        max_length=255, unique=False, db_index=False, blank=True
    )
    ci_notes = models.CharField(
        max_length=255, unique=False, db_index=False, blank=True
    )
    ci_electrical_uid = models.CharField(
        max_length=255, unique=False, db_index=False, blank=True
    )
    ci_mooring_uid = models.CharField(
        max_length=255, unique=False, db_index=False, blank=True
    )
    ci_node_uid = models.CharField(
        max_length=255, unique=False, db_index=False, blank=True
    )

    tracker = FieldTracker(
        fields=[
            "part",
        ]
    )

    class MPTTMeta:
        order_insertion_by = ["order"]

    def __str__(self):
        return self.part.name

    # method to set the object_type variable to send to Javascript AJAX functions
    def get_object_type(self):
        return "assemblyparts"

    def get_subassembly_total_cost(self):
        tree = self.get_descendants(include_self=True)
        total_cost = 0
        for item in tree:
            revision = item.part.revisions.first()
            cost = revision.unit_cost
            total_cost = total_cost + cost
        return total_cost

    def get_descendants_with_self(self):
        tree = self.get_descendants(include_self=True)
        return tree
