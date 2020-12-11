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

from roundabout.inventory.models import Inventory, Action, DeploymentAction, Deployment, InventoryDeployment
from roundabout.builds.models import Build, BuildAction


# Functions to update legacy content to match new model updates
#------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# v.1.6.1 upgrades
# v1.5 upgrades
def run_v1_6_1_content_updates():
    _update_inventory_deployments()

def _update_inventory_deployments():
    inventory_deployments = InventoryDeployment.objects.all()

    for inv in inventory_deployments:
        print(inv.inventory.assembly_part)
        inv.assembly_part = inv.inventory.assembly_part
        inv.save()

# v1.5 upgrades
def run_v1_5_content_updates():
    _update_deployment_actions()
    _update_deployment_details()
    _update_action_types()
    _update_inv_actions()
    _update_builds_actions()
    _import_old_build_actions()
    _update_build_dep_actions()
    _create_inv_deployments()


# Step 1 in migration - update DeploymentAction
def _update_deployment_actions():
    actions = DeploymentAction.objects.all()

    for action in actions:
        if action.action_type == 'create':
            action.action_type = 'startdeployment'
        elif action.action_type == 'burnin':
            action.action_type = 'deploymentburnin'
        elif action.action_type == 'deploy' or action.action_type == 'deploymenttosea':
            action.action_type = 'deploymenttofield'
        elif action.action_type == 'details':
            action.action_type = 'deploymentdetails'
        elif action.action_type == 'recover':
            action.action_type = 'deploymentrecover'
        elif action.action_type == 'retire':
            action.action_type = 'deploymentretire'
        action.save()


# Step 2 in migration
def _update_deployment_details():
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
        print(deployment)


# Action model updates for v1.5 upgrade
#------------------------------------------------------------------------------
def _update_action_types():
    actions = Action.objects.only('action_type')

    for action in actions:
        if action.action_type == 'deploymenttosea':
            action.action_type = 'deploymenttofield'

        if action.action_type == 'invadd':
            action.action_type = 'add'

        action.save()
        print(action)


# Inventory model updates for v1.5 upgrade
#------------------------------------------------------------------------------
# Update legacy Inventory Actions to add Build/Parent metadata
def _update_inv_actions():
    items = Inventory.objects.all()

    for item in items:
        last_action = item.actions.latest()

        if item.build:
            last_action.build = item.build

        if item.parent:
            last_action.parent = item.parent

        last_action.save()

# Build model updates for v1.5 upgrade
#------------------------------------------------------------------------------
# Update Build action_types
def _update_builds_actions():
    actions = BuildAction.objects.all()

    for action in actions:
        if action.action_type == 'subassemblychange':
            action.action_type = 'subchange'
        elif action.action_type == 'buildadd':
            action.action_type = 'add'
        elif action.action_type == 'deploymenttosea':
            action.action_type = 'deploymenttofield'
        elif action.action_type == 'startdeploy':
            action.action_type = 'startdeployment'
        action.save()


# Import old BuildAction objs to Action
def _import_old_build_actions():
    actions = BuildAction.objects.all()
    for action in actions:
        new_action = Action.objects.create(
            build=action.build,
            action_type=action.action_type,
            object_type='build',
            location=action.location,
            created_at=action.created_at,
            detail=action.detail,
            user=action.user,
        )


# Update legacy Build Actions if they're Deployment actions
def _update_build_dep_actions():
    builds = Build.objects.all()
    dep_action_list = ['startdeployment', 'deploymentburnin', 'deploymenttofield', 'deploymentdetails', 'deploymentrecover', 'deploymentretire']
    for build in builds:
        actions = build.get_actions()
        dep_actions = actions.filter(action_type__in=dep_action_list)
        for action in dep_actions:
            action.deployment_type = 'build_deployment'
            action.deployment = build.get_latest_deployment()
            action.save()
            print(action)


# Create new InventoryDeployment objects for items that are already on deployment
def _create_inv_deployments():
    builds = Build.objects.filter(is_deployed=True)
    for build in builds:
        print(build)
        for item in build.inventory.all():
            print(item, build.current_deployment(), build.current_deployment().deployment_start_date)
            # Create InventoryDeployment record
            inventory_deployment = InventoryDeployment.objects.create(
                deployment=build.current_deployment(),
                inventory=item,
                deployment_start_date = build.current_deployment().deployment_start_date,
                deployment_burnin_date = build.current_deployment().deployment_burnin_date,
                deployment_to_field_date = build.current_deployment().deployment_to_field_date,
                deployment_recovery_date = build.current_deployment().deployment_recovery_date,
                current_status = build.current_deployment().current_status,
            )
            print(inventory_deployment, inventory_deployment.current_status)
