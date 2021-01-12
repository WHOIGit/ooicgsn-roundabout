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
from django.utils import timezone

from .models import *
from roundabout.inventory.models import Inventory
from roundabout.builds.models import Build
# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels
labels = set_app_labels()

# Utility functions for use with Inventory models
# ------------------------------------------------------------------------------

# Function to handle creating new Action records with meta data for different Action.OBJECT_TYPES
# Current objects available = Inventory, Build
def _create_action_history(obj, action_type, user, referring_obj=None, referring_action='', action_date=None):
    # Set default variables
    object_type = obj._meta.model_name
    detail = ''
    deployment = None
    if not action_date:
        action_date = timezone.now()

    if (object_type == Action.BUILD or object_type == Action.INVENTORY or object_type == Action.CALEVENT or object_type == Action.CONSTDEFEVENT or object_type == Action.CONFEVENT or object_type == Action.CONFDEFEVENT or object_type == Action.COEFFNAMEEVENT or object_type == Action.CONFNAMEEVENT) and not referring_obj:
        detail = obj.detail

    # reset obj.detail for next loop
    if detail:
        obj.detail = ''
        obj.save()

    # create primary Action record
    action_record = Action()
    action_record.action_type = action_type
    action_record.object_type = object_type
    action_record.user = user
    if hasattr(obj, 'location'):
        action_record.location = obj.location
    action_record.detail = detail
    action_record.created_at = action_date

    # set deployment_type by checking if a Build object started the action
    if isinstance(obj, Build) or isinstance(referring_obj, Build):
        deployment_type = Action.BUILD_DEPLOYMENT
    else:
        deployment_type = Action.INVENTORY_DEPLOYMENT

    # set the primary object this record refers to
    if object_type == Action.BUILD:
        obj_label = labels['label_builds_app_singular']
        action_record.build = obj
        deployment = obj.current_deployment()
        # Set extra meta data fields
        action_record.deployment = deployment

    elif object_type == Action.INVENTORY:
        obj_label = labels['label_inventory_app_singular']
        action_record.inventory = obj
        action_record.parent = obj.parent

        if obj.build:
            deployment = obj.build.current_deployment()
        # Set extra meta data fields
        action_record.build = obj.build
        action_record.deployment = deployment

    elif object_type == Action.CALEVENT:
        obj_label = 'Calibration Event'
        action_record.calibration_event = obj

    elif object_type == Action.CONSTDEFEVENT:
        obj_label = 'Constant Default Event'
        action_record.const_default_event = obj

    elif object_type == Action.CONFEVENT:
        obj_label = 'Configuration Event'
        action_record.config_event = obj

    elif object_type == Action.CONFDEFEVENT:
        obj_label = 'Configuration Default Event'
        action_record.config_default_event = obj

    elif object_type == Action.COEFFNAMEEVENT:
        obj_label = 'Calibration(s)'
        action_record.coefficient_name_event = obj

    elif object_type == Action.CONFNAMEEVENT:
        obj_label = 'Configuration(s)'
        action_record.config_name_event = obj

    # Run through the discrete Actions, set up details text and extra records if needed.
    if action_type == Action.ADD:
        action_record.detail = '%s first added to RDB. %s' % (obj_label, detail)
        action_record.save()

    elif action_type == Action.UPDATE:
        action_record.detail = '%s details updated.' % (obj_label)
        action_record.save()

    elif action_type == Action.LOCATIONCHANGE or action_type == Action.MOVETOTRASH:
        action_record.detail = 'Moved to %s from %s. %s' % (obj.location, obj.actions.latest().location, detail)
        action_record.save()

        if action_type == Action.MOVETOTRASH:
            if obj.get_latest_build():
                _create_action_history(obj, Action.REMOVEFROMBUILD, user)

    elif action_type == Action.SUBCHANGE:
        if obj.location_changed():
            _create_action_history(obj, Action.LOCATIONCHANGE, user)

        if referring_obj:
            if object_type == Action.INVENTORY:
                if obj.is_leaf_node():
                    action_record.detail = 'Sub-%s %s removed.' % (labels['label_assemblies_app_singular'], referring_obj)
                else:
                    action_record.detail = 'Sub-%s %s added.' % (labels['label_assemblies_app_singular'], referring_obj)
            else:
                if referring_action == Action.ADDTOBUILD:
                    action_record.detail = 'Sub-%s %s added.' % (labels['label_assemblies_app_singular'], referring_obj)
                else:
                    action_record.detail = 'Sub-%s %s removed.' % (labels['label_assemblies_app_singular'], referring_obj)
        else:
            if obj.parent:
                action_record.detail = 'Added to %s.' % (obj.parent)
            else:
                action_record.detail = 'Removed from %s.' % (obj.get_latest_parent())
                _create_action_history(obj.get_latest_parent(), Action.SUBCHANGE, user, obj)
        action_record.save()

    elif action_type == Action.ADDTOBUILD:
        if obj.location_changed():
            _create_action_history(obj, Action.LOCATIONCHANGE, user, '', '', action_date)

        action_record.detail = 'Moved to %s.' % (obj.build)
        action_record.save()

        if not referring_obj:
            if obj.parent:
                _create_action_history(obj, Action.SUBCHANGE, user, '', '', action_date)
                _create_action_history(obj.parent, Action.SUBCHANGE, user, obj, '', action_date)

        # If Build is deployed, need to add extra Action record to add to Deployment
        if obj.build.is_deployed:
            _create_action_history(obj, Action.STARTDEPLOYMENT, user, '', '', action_date)
            if obj.build.current_deployment().current_status == Action.DEPLOYMENTBURNIN:
                _create_action_history(obj, Action.DEPLOYMENTBURNIN, user, '', '', action_date)

        # Add Action record for the Build
        _create_action_history(obj.get_latest_build(), Action.SUBCHANGE, user, obj, action_type, action_date)

    elif action_type == Action.REMOVEFROMBUILD:
        if obj.location_changed():
            _create_action_history(obj, Action.LOCATIONCHANGE, user, '', '', action_date)

        action_record.build = obj.get_latest_build()
        action_record.detail = 'Removed from %s. %s' % (obj.get_latest_build(), detail)
        action_record.location = obj.get_latest_build().location
        action_record.save()

        if not referring_obj and obj.parent_changed():
            _create_action_history(obj, Action.SUBCHANGE, user)
            _create_action_history(obj.get_latest_parent(), Action.SUBCHANGE, user, obj)

        # If Build is deployed, need to add extra Action record to add to Deployment
        if obj.get_latest_build().is_deployed:
            _create_action_history(obj, Action.DEPLOYMENTRETIRE, user, '', '', action_date)

        # Add Action record for the Build
        _create_action_history(obj.get_latest_build(), Action.SUBCHANGE, user, obj, action_type, action_date)

    elif action_type == Action.ASSIGNDEST:
        action_record.detail = 'Destination assigned - %s.' % (obj.assembly_part.assembly_revision)
        action_record.save()

    elif action_type == Action.REMOVEDEST:
        action_record.detail = 'Destination Assignment removed. %s' % (detail)
        action_record.save()

    elif action_type == Action.TEST:
        action_record.detail = '%s: %s. %s' % (obj.get_test_type_display(), obj.get_test_result_display(), detail)
        action_record.save()

    elif action_type == Action.STARTDEPLOYMENT:
        if obj.location_changed():
            _create_action_history(obj, Action.LOCATIONCHANGE, user, '', '', action_date)

        action_record.detail = '%s %s started' % (labels['label_deployments_app_singular'], deployment)
        action_record.deployment_type = deployment_type
        if deployment_type == Action.BUILD_DEPLOYMENT:
            action_record.created_at = deployment.deployment_start_date

        if isinstance(obj, Inventory):
            # Create InventoryDeployment record
            inventory_deployment = InventoryDeployment.objects.create(
                deployment=deployment,
                inventory=obj,
                assembly_part=obj.assembly_part,
                deployment_start_date = action_date
            )
            action_record.inventory_deployment = inventory_deployment
        action_record.save()

    elif action_type == Action.DEPLOYMENTBURNIN:
        if obj.location_changed():
            _create_action_history(obj, Action.LOCATIONCHANGE, user, '', '', action_date)

        action_record.detail = '%s %s burn in' % (labels['label_deployments_app_singular'], deployment)
        action_record.created_at = deployment.deployment_burnin_date
        action_record.deployment_type = deployment_type

        if isinstance(obj, Inventory):
            # Update InventoryDeployment record
            inventory_deployment = obj.inventory_deployments.get_active_deployment()
            inventory_deployment.deployment_burnin_date = action_date
            inventory_deployment.save()
            action_record.inventory_deployment = inventory_deployment
            action_record.created_at = action_date
        action_record.save()

    elif action_type == Action.DEPLOYMENTTOFIELD:
        if obj.location_changed():
            _create_action_history(obj, Action.LOCATIONCHANGE, user, '', '', action_date)

        action_record.detail = 'Deployed to field on %s.' % (deployment)
        action_record.created_at = deployment.deployment_to_field_date
        action_record.deployment_type = deployment_type
        action_record.latitude = deployment.latitude
        action_record.longitude = deployment.longitude
        action_record.depth = deployment.depth

        if isinstance(obj, Build):
            action_record.cruise = deployment.cruise_deployed
            action_record.detail = '%s Cruise: %s' % (action_record.detail, deployment.cruise_deployed)

        # Update InventoryDeployment record
        if isinstance(obj, Inventory):
            inventory_deployment = obj.inventory_deployments.get_active_deployment()
            # Only update date/cruise on full Build deployment, not individual item
            if deployment_type == Action.BUILD_DEPLOYMENT:
                inventory_deployment.deployment_to_field_date = action_date
                inventory_deployment.cruise_deployed = deployment.cruise_deployed
            else:
                inventory_deployment.deployment_start_date = action_date

            inventory_deployment.save()
            action_record.inventory_deployment = inventory_deployment
            action_record.created_at = action_date
            action_record.cruise = inventory_deployment.cruise_deployed
            action_record.detail = '%s Cruise: %s' % (action_record.detail, inventory_deployment.cruise_deployed)
        action_record.save()

    elif action_type == Action.DEPLOYMENTRECOVER:
        if obj.location_changed():
            _create_action_history(obj, Action.LOCATIONCHANGE, user, '', '', action_date)

        deployment = obj.get_latest_deployment()
        action_record.detail = 'Recovered from %s. %s' % (deployment, detail)
        action_record.deployment_type = deployment_type
        action_record.deployment = deployment

        if isinstance(obj, Build):
            action_record.cruise = deployment.cruise_recovered
            action_record.detail = '%s Cruise: %s' % (action_record.detail, deployment.cruise_recovered)

        # Update InventoryDeployment record
        if isinstance(obj, Inventory):
            inventory_deployment = obj.inventory_deployments.get_active_deployment()
            # Only update date/cruise on full Build deployment, not individual item
            if deployment_type == Action.BUILD_DEPLOYMENT:
                inventory_deployment.deployment_recovery_date = action_date
                inventory_deployment.cruise_recovered = deployment.cruise_recovered
            inventory_deployment.save()
            action_record.inventory_deployment = inventory_deployment
            action_record.build = obj.get_latest_build()
            action_record.detail = 'Recovered from %s. %s' % (deployment, detail)
            action_record.created_at = action_date
            action_record.cruise = inventory_deployment.cruise_recovered
            action_record.detail = '%s Cruise: %s' % (action_record.detail, inventory_deployment.cruise_recovered)

        action_record.save()
        # Run secondary Action records after completion
        if deployment_type == Action.INVENTORY_DEPLOYMENT:
            # Add Remove from Build record
            _create_action_history(obj, Action.REMOVEFROMBUILD, user, '', '', action_date)

    elif action_type == Action.DEPLOYMENTRETIRE:
        deployment = obj.get_latest_deployment()
        action_record.deployment = deployment
        action_record.detail = '%s %s ended for this %s.' % (labels['label_deployments_app_singular'], deployment, obj_label)
        # update InventoryDeployment record
        if isinstance(obj, Inventory):
            inventory_deployment = obj.inventory_deployments.get_active_deployment()
            if inventory_deployment:
                inventory_deployment.deployment_retire_date = action_date
                inventory_deployment.save()
                action_record.inventory_deployment = inventory_deployment
        action_record.save()

    elif action_type == Action.REVIEWAPPROVE:
        action_record.detail = 'Reviewer approved %s. %s' % (obj_label, detail)
        action_record.save()

    elif action_type == Action.EVENTAPPROVE:
        action_record.detail = '%s Approved. %s' % (obj_label, detail)
        action_record.save()
    elif action_type == Action.CALCSVIMPORT:
        action_record.detail = '%s Created via CSV Import. %s' % (obj_label, detail)
        action_record.save()
    else:
        action_record.save()

    """
    # loop through any children
    if object_type == Action.INVENTORY:
        if not referring_obj and obj.get_children().exists():
            for child in obj.get_children():
                _create_action_history(child, action_type, user, obj)
    """
    return action_record
