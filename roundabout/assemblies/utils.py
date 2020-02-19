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

from .models import Assembly, AssemblyPart, AssemblyType, AssemblyDocument, AssemblyRevision

# Utility functions for use with Assembly models
# ------------------------------------------------------------------------------

# Functions to migrate legacy Assemblies to new Assembly Revision version
# ------------------------------------------------------------------------------
# Create a new default "A" revision for all existing Assemblies - Step 1 in migration
def create_default_first_revision():
    assemblies_qs = Assembly.objects.all()
    for assembly in assemblies_qs:
        revision = AssemblyRevision.objects.create(assembly=assembly, revision_code='A')
        message = '%s - %s' % (assembly, revision)
        print(message)


# Move all existing Assembly Parts to the new Revision, remove link to parent Assembly
def move_assemblyparts_to_revision():
    assemblies_qs = Assembly.objects.all()
    for assembly in assemblies_qs:
        revision = assembly.assembly_revisions.last()
        assembly_parts = assembly.assembly_parts.all()
        for ap in assembly_parts:
            ap.assembly_revision = revision
            ap.assembly = None
            ap.save()
            print(ap)
