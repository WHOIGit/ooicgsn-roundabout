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

# Utility functions for use with Inventory models
# ------------------------------------------------------------------------------

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
