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

# Import environment variables from .env files
import environ
env = environ.Env()

# Set sitewide variables for headings/labels display
# Uses environmental variables from .env files
# These are then used in context_processors for templates and forms.py for form labels

def set_app_labels():
    # Set pattern variables from .env configuration
    RDB_LABEL_ASSEMBLIES_SINGULAR = env('RDB_LABEL_ASSEMBLIES_SINGULAR', default='Assembly')
    RDB_LABEL_ASSEMBLIES_PLURAL = env('RDB_LABEL_ASSEMBLIES_PLURAL', default='Assemblies')
    RDB_LABEL_BUILDS_SINGULAR = env('RDB_LABEL_BUILDS_SINGULAR', default='Build')
    RDB_LABEL_BUILDS_PLURAL = env('RDB_LABEL_BUILDS_PLURAL', default='Builds')
    RDB_LABEL_DEPLOYMENTS_SINGULAR = env('RDB_LABEL_DEPLOYMENTS_SINGULAR', default='Deployment')
    RDB_LABEL_DEPLOYMENTS_PLURAL = env('RDB_LABEL_DEPLOYMENTS_PLURAL', default='Deployments')
    RDB_LABEL_INVENTORY_SINGULAR = env('RDB_LABEL_INVENTORY_SINGULAR', default='Inventory')
    RDB_LABEL_INVENTORY_PLURAL = env('RDB_LABEL_INVENTORY_PLURAL', default='Inventory')

    labels = {
        # Assemblies
        'label_assemblies_app_singular': RDB_LABEL_ASSEMBLIES_SINGULAR,
        'label_assemblies_app_plural': RDB_LABEL_ASSEMBLIES_PLURAL,
        # Builds
        'label_builds_app_singular': RDB_LABEL_BUILDS_SINGULAR,
        'label_builds_app_plural': RDB_LABEL_BUILDS_PLURAL,
        # Deployments
        'label_deployments_app_singular': RDB_LABEL_DEPLOYMENTS_SINGULAR,
        'label_deployments_app_plural': RDB_LABEL_DEPLOYMENTS_PLURAL,
        # Deployments
        'label_inventory_app_singular': RDB_LABEL_INVENTORY_SINGULAR,
        'label_inventory_app_plural': RDB_LABEL_INVENTORY_PLURAL,
    }

    return labels
