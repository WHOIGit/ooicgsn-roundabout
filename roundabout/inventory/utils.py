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

from .models import *
# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels
labels = set_app_labels()

# Utility functions for use with Inventory models
# ------------------------------------------------------------------------------

def _create_action_history(obj, action_type, user, referring_obj=None, referring_action=''):
    # Set default variables
    object_type = obj._meta.model_name
    detail = ''
    deployment = None

    if not referring_obj:
        detail = obj.detail
    # reset obj.detail for next loop
    if detail:
        obj.detail = ''
        obj.save()

    # primary Action record
    action_record = Action()
    action_record.action_type = action_type
    action_record.object_type = object_type
    action_record.user = user
    action_record.location = obj.location
    action_record.detail = detail

    # set the primary object this record refers to
    if object_type == Action.BUILD:
        action_record.build = obj
        obj_label = labels['label_builds_app_singular']
        deployment = obj.current_deployment()
        deployment_type = Action.BUILD_DEPLOYMENT
        # Set extra meta data fields
        action_record.deployment = deployment

    elif object_type == Action.INVENTORY:
        action_record.inventory = obj
        action_record.parent = obj.parent
        obj_label = labels['label_inventory_app_singular']

        if obj.build:
            deployment = obj.build.current_deployment()
            deployment_type = Action.INVENTORY_DEPLOYMENT
        # Set extra meta data fields
        action_record.build = obj.build
        action_record.deployment = deployment

    elif object_type == Action.DEPLOYMENT:
        action_record.deployment = obj
        obj_label = labels['label_deployments_app_singular']

    # Run through the discrete Actions, set up details text and extra records if needed.
    if action_type == Action.ADD:
        action_record.detail = '%s first added to RDB. %s' % (obj_label, detail)

    elif action_type == Action.LOCATIONCHANGE or action_type == Action.MOVETOTRASH:
        action_record.detail = 'Moved to %s from %s. %s' % (obj.location, obj.actions.latest().location, detail)

        if action_type == Action.MOVETOTRASH:
            if obj.get_latest_build():
                _create_action_history(obj, Action.REMOVEFROMBUILD, user)
                # If Build is Deployed, need to create separate Deployment Retirement record,
                if obj.get_latest_build().is_deployed:
                    _create_action_history(obj, Action.DEPLOYMENTRETIRE, user)
                # Create Build Action record
                # Add Action record for the Build
                _create_action_history(obj.get_latest_build(), Action.SUBCHANGE, user, obj, action_type)

    elif action_type == Action.SUBCHANGE:
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

    elif action_type == Action.ADDTOBUILD:
        action_record.detail = 'Moved to %s.' % (obj.build)

        if obj.location_changed():
            _create_action_history(obj, Action.LOCATIONCHANGE, user)

        if not referring_obj:
            if obj.parent:
                _create_action_history(obj, Action.SUBCHANGE, user)
                _create_action_history(obj.parent, Action.SUBCHANGE, user, obj)

        # If Build is deployed, need to add extra Action record to add to Deployment
        if obj.build.is_deployed:
            _create_action_history(obj, Action.STARTDEPLOYMENT, user)
            if build.current_deployment().current_status == Action.DEPLOYMENTBURNIN:
                _create_action_history(obj, Action.DEPLOYMENTBURNIN, user)

        # Add Action record for the Build
        _create_action_history(obj.get_latest_build(), Action.SUBCHANGE, user, obj, action_type)

    elif action_type == Action.REMOVEFROMBUILD:
        action_record.build = obj.get_latest_build()
        action_record.detail = 'Removed from %s. %s' % (obj.get_latest_build(), detail)
        action_record.location = obj.get_latest_build().location

        if obj.location_changed():
            _create_action_history(obj, Action.LOCATIONCHANGE, user)

        if not referring_obj and obj.parent_changed():
            _create_action_history(obj, Action.SUBCHANGE, user)
            _create_action_history(obj.get_latest_parent(), Action.SUBCHANGE, user, obj)

        # If Build is deployed, need to add extra Action record to add to Deployment
        if obj.get_latest_build().is_deployed:
            _create_action_history(obj, Action.DEPLOYMENTRETIRE, user)

        # Add Action record for the Build
        _create_action_history(obj.get_latest_build(), Action.SUBCHANGE, user, obj, action_type)

    elif action_type == Action.ASSIGNDEST:
        detail = 'Destination assigned - %s.' % (self.assembly_part.assembly_revision)

    elif action_type == Action.REMOVEDEST:
        detail = 'Destination Assignment removed. %s' % (detail)

    elif action_type == Action.TEST:
        action_record.detail = '%s: %s. %s' % (obj.get_test_type_display(), obj.get_test_result_display(), detail)

    elif action_type == Action.STARTDEPLOYMENT:
        action_record.detail = '%s %s started' % (labels['label_deployments_app_singular'], deployment)
        if deployment_type == Action.INVENTORY_DEPLOYMENT:
            # Create InventoryDeployment record
            inventory_deployment = InventoryDeployment.objects.create(
                deployment=deployment,
                inventory=obj,
            )
    elif action_type == Action.DEPLOYMENTBURNIN:
        action_record.detail = '%s %s burn in' % (labels['label_deployments_app_singular'], deployment)
        if deployment_type == Action.INVENTORY_DEPLOYMENT:
            # Update InventoryDeployment record
            inventory_deployment = obj.inventory_deployments.get_active_deployment()
            inventory_deployment.deployment_burnin_date = created_at
            inventory_deployment.save()

    elif action_type == Action.DEPLOYMENTTOFIELD:
        action_record.detail = 'Deployed to field on %s.' % (deployment)
        if cruise:
            action_record.detail = '%s Cruise: %s' % (action_record.detail, cruise)
        # Update InventoryDeployment record
        inventory_deployment = self.inventory_deployments.get_active_deployment()
        inventory_deployment.deployment_to_field_date = created_at
        inventory_deployment.cruise_deployed = cruise
        inventory_deployment.save()
    elif action_type == Action.DEPLOYMENTRECOVER:
        build = self.get_latest_build()
        deployment = self.get_latest_deployment()
        action_record.detail = 'Recovered from %s. %s' % (deployment, detail)
        if cruise:
            detail = '%s Cruise: %s' % (detail, cruise)
        # update InventoryDeployment record
        inventory_deployment = self.inventory_deployments.get_active_deployment()
        inventory_deployment.deployment_recovery_date = created_at
        inventory_deployment.cruise_recovered = cruise
        inventory_deployment.save()
    elif action_type == Action.DEPLOYMENTRETIRE:
        build = self.get_latest_build()
        deployment = self.get_latest_deployment()
        action_record.detail = '%s %s ended for this item.' % (labels['label_deployments_app_singular'], deployment)
        # update InventoryDeployment record
        inventory_deployment = self.inventory_deployments.get_active_deployment()
        inventory_deployment.deployment_retire_date = created_at
        inventory_deployment.save()

    action_record.save()
    """
    # loop through any children
    if object_type == Action.INVENTORY:
        if not referring_obj and obj.get_children().exists():
            for child in obj.get_children():
                _create_action_history(child, action_type, user, obj)
    """
    return action_record

# Functions to migrate legacy Assemblies to new Assembly Revision version
# ------------------------------------------------------------------------------
# Step 1 in migration
def update_deployment_actions():
    actions = DeploymentAction.objects.all()
    for action in actions:
        if action.action_type == 'create':
            action.action_type = 'startdeployment'
        elif action.action_type == 'burnin':
            action.action_type = 'deploymentburnin'
        elif action.action_type == 'deploy':
            action.action_type = 'deploymenttofield'
        elif action.action_type == 'details':
            action.action_type = 'deploymentdetails'
        elif action.action_type == 'recover':
            action.action_type = 'deploymentrecover'
        elif action.action_type == 'retire':
            action.action_type = 'deploymentretire'
        action.save()
        print(action)


# Step 2 in migration
def update_deployment_details():
    deployments = Deployment.objects.all()
    for deployment in deployments:
        # get the latest 'Deploy' action record to initial
        start_record = DeploymentAction.objects.filter(deployment=deployment).filter(action_type='startdeployment').first()
        # get the latest 'Deploy' action record to initial
        burnin_record = DeploymentAction.objects.filter(deployment=deployment).filter(action_type='deploymentburnin').first()
        # get the latest 'Deploy' action record to initial
        deploy_record = DeploymentAction.objects.filter(deployment=deployment).filter(action_type='deploymenttofield').first()
        # get the latest 'Detail' action record to find last lat/long/depth data
        detail_record = DeploymentAction.objects.filter(deployment=deployment).filter(action_type='deploymentdetails').first()
        # get the latest 'Detail' action record to find last lat/long/depth data
        recover_record = DeploymentAction.objects.filter(deployment=deployment).filter(action_type='deploymentrecover').first()
        # get the latest 'Detail' action record to find last lat/long/depth data
        retire_record = DeploymentAction.objects.filter(deployment=deployment).filter(action_type='deploymentretire').first()

        if start_record:
            deployment.deployment_start_date = start_record.created_at
            deployment.current_status = 'startdeployment'

        if burnin_record:
            deployment.deployment_burnin_date = burnin_record.created_at
            deployment.current_status = 'deploymentburnin'

        if deploy_record:
            deployment.deployment_to_field_date = deploy_record.created_at
            deployment.current_status = 'deploymenttofield'

        if detail_record:
            deployment.latitude = detail_record.latitude
            deployment.longitude = detail_record.longitude
            deployment.depth = detail_record.depth

        if recover_record:
            deployment.deployment_recovery_date = recover_record.created_at
            deployment.current_status = 'deploymentrecover'

        if retire_record:
            deployment.deployment_retire_date = retire_record.created_at
            deployment.current_status = 'deploymentretire'

        deployment.save()
        message = '%s saved' % (deployment)
        print(message)
