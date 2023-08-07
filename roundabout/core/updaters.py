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

from roundabout.inventory.models import (
    Inventory,
    Action,
    DeploymentAction,
    Deployment,
    InventoryDeployment,
)
from roundabout.builds.models import Build, BuildAction
from roundabout.assemblies.models import AssemblyPart
from roundabout.ooi_ci_tools.models import (
    ReferenceDesignatorEvent,
    ReferenceDesignator,
    Comment,
    MPTTComment,
    CruiseEvent,
    VesselEvent
)
from roundabout.cruises.models import Cruise, Vessel
from roundabout.parts.models import Part
from roundabout.exports.views import ExportDeployments
from roundabout.inventory.utils import _create_action_history


# Generate Cruise Events for legacy Cruises created prior to Event system
def _update_cruise_events():
    for cruise in Cruise.objects.all():
        if not hasattr(cruise, "cruise_event"):
            print("adding cruise event")
            new_cruise_event = CruiseEvent.objects.create(cruise=cruise)
            new_cruise_event.save()
        else:
            print("Cruise event already exists")


# Generate Reference Designator Event and Reference Designator Values from Assemblyparts containing Configuration Defaults with populated Reference Designator Config Names
def _create_reference_designators():
    for assm_part in AssemblyPart.objects.all():
        if assm_part.assemblypart_configdefaultevents.exists():
            for (dflt) in (assm_part.assemblypart_configdefaultevents.first().config_defaults.all()):
                if dflt.config_name.name == "Reference Designator":
                    if len(dflt.default_value) >= 1:
                        try:
                            (
                                refdes_event,
                                refdes_event_created,
                            ) = ReferenceDesignatorEvent.objects.get_or_create(
                                assembly_part=assm_part
                            )
                        except ReferenceDesignatorEvent.MultipleObjectsReturned:
                            refdes_event = ReferenceDesignatorEvent.objects.filter(
                                assembly_part=assm_part
                            ).first()
                            refdes_event_created = False
                        if refdes_event_created:
                            _create_action_history(refdes_event, Action.ADD, user=None)
                        try:
                            (
                                refdes_value,
                                refdes_value_created
                            ) = ReferenceDesignator.objects.get_or_create(
                                refdes_name=dflt.default_value
                            )
                        except ReferenceDesignator.MultipleObjectsReturned:
                            refdes_value = ReferenceDesignator.objects.filter(
                                refdes_name=dflt.default_value
                            ).first()
                            refdes_value_created = False

                        refdes_event.reference_designator = refdes_value
                        assm_part.reference_designator = refdes_value
                        refdes_event.save()
                        assm_part.save()


# Create MPTTComments based on existing Comment parent/child relationships
# from roundabout.core.updaters import _create_mptt_comments
# _create_mptt_comments()
def _create_mptt_comments():
    comments = Comment.objects.all()
    MPTTComment.objects.all().delete()
    for comment in comments:
        MPTTComment.objects.create(
            action=comment.action, user=comment.user, detail=comment.detail
        )
    for comment in comments:
        if comment.parent:
            parent = comment.parent
            mptt_parent = MPTTComment.objects.get(
                action=parent.action, user=parent.user, detail=parent.detail
            )
            mptt_child = MPTTComment.objects.get(
                action=comment.action, user=comment.user, detail=comment.detail
            )
            mptt_child.parent = mptt_parent
            mptt_child.save()


# For Parts with zeroed-out Max Calibration Decimal Places, set default value to 32 places
def _update_part_decimal_default():
    for part in Part.objects.all():
        if not part.cal_dec_places:
            part.cal_dec_places = 32
            part.save()


def remove_extra_actions():
    builds = Build.objects.all()
    for build in builds:
        print(build)
        build_actions = build.get_actions()
        actions_to_keep = []
        for action in build_actions:
            dup_action = (
                build.get_actions()
                .filter(detail=action.detail, created_at=action.created_at)
                .exclude(id=action.id)
                .exclude(id__in=actions_to_keep)
            )
            print(dup_action.count())
            if dup_action:
                dup_action.delete()
                actions_to_keep.append(action.id)


# v.1.7.0 upgrades
def run_v1_7_0_content_updates():
    print("Running: v1.7.0 Content Updates")
    _update_action_data()
    print("\nCOMPLETE: v1.7.0 Content Updates")


def _update_action_data():
    print("\nVESSELS")
    _update_action_data_vessels()
    print("\nCRUISES")
    _update_action_data_cruises()
    print("\nCALEVENTS")
    _update_action_data_CalEvts()
    print("\nCONFEVENTS")
    _update_action_data_ConfEvts()
    print("\nDEPLOYMENTS")
    _update_action_data_deployments()


def _update_action_data_vessels():
    vessels = Vessel.objects.filter(actions__isnull=True)
    if not vessels:
        return print("  No Vessels to update")
    fields = [field.name for field in Vessel._meta.fields if field.name != "id"]
    print("fields:", ",".join(fields))
    for vessel in vessels:
        print(" ", vessel.vessel_name)
        updated_values = dict()
        for field in fields:
            val = getattr(vessel, field, None)
            if val:
                updated_values[field] = {"from": None, "to": str(val)}
        data = dict(updated_values=updated_values) if updated_values else None
        if vessel.cruises.exists():
            _create_action_history(
                vessel,
                Action.ADD,
                user=None,
                data=data,
                action_date=vessel.cruises.first().cruise_start_date,
            )


def _update_action_data_cruises():
    cruises = Cruise.objects.all()
    cruises = [
        cruise
        for cruise in cruises
        if not cruise.actions.filter(action_type=Action.ADD).exists()
    ]
    if not cruises:
        return print("  No Cruises to update")
    fields = [field.name for field in Cruise._meta.fields if field.name != "id"]
    print("fields:", ",".join(fields))
    for cruise in cruises:
        print(" ", cruise.CUID)
        updated_values = dict()
        for field in fields:
            val = getattr(cruise, field, None)
            if val:
                updated_values[field] = {"from": None, "to": str(val)}
        data = dict(updated_values=updated_values) if updated_values else None
        _create_action_history(
            cruise,
            Action.ADD,
            user=None,
            data=data,
            action_date=cruise.cruise_start_date,
        )


def _update_action_data_CalEvts():
    cal_actions = Action.objects.filter(
        action_type=Action.ADD, object_type=Action.CALEVENT, data__isnull=True
    )
    if not cal_actions:
        return print("  No CalibrationEvents to update")
    for action in cal_actions:
        print("  id:", action.calibration_event.id, action)
        data = {}
        updated_values = {}
        updated_notes = {}
        init_CoefficientValueSets = (
            action.calibration_event.coefficient_value_sets.all()
        )
        for val in init_CoefficientValueSets:
            if val.value_set:
                updated_values[val.coefficient_name.calibration_name] = {
                    "from": None,
                    "to": val.value_set,
                }
            if val.notes:
                updated_notes[val.coefficient_name.calibration_name] = {
                    "from": None,
                    "to": val.notes,
                }
        if updated_values:
            data["updated_values"] = updated_values
        if updated_notes:
            data["updated_notes"] = updated_notes
        action.data = data
        action.save()


def _update_action_data_ConfEvts():
    conf_actions = Action.objects.filter(
        action_type=Action.ADD, object_type=Action.CONFEVENT, data__isnull=True
    )
    if not conf_actions:
        return print("  No ConfigEvents to update")
    for action in conf_actions:
        print("  id:", action.config_event.id, action)
        data = {}
        updated_values = {}
        updated_notes = {}
        init_ConfigValues = action.config_event.config_values.all()
        for val in init_ConfigValues:
            if val.config_value:
                updated_values[val.config_name.name] = {
                    "from": None,
                    "to": val.config_value,
                }
            if val.notes:
                updated_notes[val.config_name.name] = {"from": None, "to": val.notes}
        if updated_values:
            data["updated_values"] = updated_values
        if updated_notes:
            data["updated_notes"] = updated_notes
        action.data = data
        action.save()


def _update_action_data_deployments():
    deployments = Deployment.objects.all()
    fields = [a for h, a in ExportDeployments.header_att if a]
    print("fields:", ",".join(fields))
    any_updates = False
    for deployment in deployments:
        actions = Action.objects.filter(deployment__pk=deployment.pk).exclude(
            data__isnull=True
        )
        if actions.exists():
            continue  # this deployment already has some Action data, skip
        else:
            any_updates = True
        print(" ", deployment)
        updated_values = dict()
        for field in fields:
            val = getattr(deployment, field, None)
            if val:
                updated_values[field] = {"from": None, "to": str(val)}
        data = dict(updated_values=updated_values) if updated_values else None
        _create_action_history(deployment, Action.UPDATE, user=None, data=data)
    if any_updates == False:
        print("  No Deployments to update")


# Functions to update legacy content to match new model updates
# ------------------------------------------------------------------------------
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
    print("Step 1")
    _update_deployment_actions()
    print("Step 2")
    _update_deployment_details()
    print("Step 3")
    _update_action_types()
    print("Step 4")
    _update_inv_actions()
    print("Step 5")
    _update_builds_actions()

    print("Step 6")
    _import_old_build_actions()
    print("Step 7")
    _update_build_dep_actions()
    print("Step 8")
    _create_inv_deployments()


# Step 1 in migration - update DeploymentAction
def _update_deployment_actions():
    actions = DeploymentAction.objects.all()

    for action in actions:
        if action.action_type == "create":
            action.action_type = "startdeployment"
        elif action.action_type == "burnin":
            action.action_type = "deploymentburnin"
        elif action.action_type == "deploy" or action.action_type == "deploymenttosea":
            action.action_type = "deploymenttofield"
        elif action.action_type == "details":
            action.action_type = "deploymentdetails"
        elif action.action_type == "recover":
            action.action_type = "deploymentrecover"
        elif action.action_type == "retire":
            action.action_type = "deploymentretire"
        action.save()


# Step 2 in migration
def _update_deployment_details():
    deployments = Deployment.objects.all()
    for deployment in deployments:
        # get the latest 'Deploy' action record to initial
        start_record = (
            DeploymentAction.objects.filter(deployment=deployment)
            .filter(action_type="startdeployment")
            .first()
        )
        # get the latest 'Deploy' action record to initial
        burnin_record = (
            DeploymentAction.objects.filter(deployment=deployment)
            .filter(action_type="deploymentburnin")
            .first()
        )
        # get the latest 'Deploy' action record to initial
        deploy_record = (
            DeploymentAction.objects.filter(deployment=deployment)
            .filter(action_type="deploymenttofield")
            .first()
        )
        # get the latest 'Detail' action record to find last lat/long/depth data
        detail_record = (
            DeploymentAction.objects.filter(deployment=deployment)
            .filter(action_type="deploymentdetails")
            .first()
        )
        # get the latest 'Detail' action record to find last lat/long/depth data
        recover_record = (
            DeploymentAction.objects.filter(deployment=deployment)
            .filter(action_type="deploymentrecover")
            .first()
        )
        # get the latest 'Detail' action record to find last lat/long/depth data
        retire_record = (
            DeploymentAction.objects.filter(deployment=deployment)
            .filter(action_type="deploymentretire")
            .first()
        )

        if start_record:
            deployment.deployment_start_date = start_record.created_at
            deployment.current_status = "startdeployment"

        if burnin_record:
            deployment.deployment_burnin_date = burnin_record.created_at
            deployment.current_status = "deploymentburnin"

        if deploy_record:
            deployment.deployment_to_field_date = deploy_record.created_at
            deployment.current_status = "deploymenttofield"

        if detail_record:
            deployment.latitude = detail_record.latitude
            deployment.longitude = detail_record.longitude
            deployment.depth = detail_record.depth

        if recover_record:
            deployment.deployment_recovery_date = recover_record.created_at
            deployment.current_status = "deploymentrecover"

        if retire_record:
            deployment.deployment_retire_date = retire_record.created_at
            deployment.current_status = "deploymentretire"

        deployment.save()
        print(deployment)


# Action model updates for v1.5 upgrade
# ------------------------------------------------------------------------------
def _update_action_types():
    actions = Action.objects.only("action_type")

    for action in actions:
        if action.action_type == "deploymenttosea":
            action.action_type = "deploymenttofield"

        if action.action_type == "invadd":
            action.action_type = "add"

        action.save()
        print(action)


# Inventory model updates for v1.5 upgrade
# ------------------------------------------------------------------------------
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
        print(item)


# Build model updates for v1.5 upgrade
# ------------------------------------------------------------------------------
# Update Build action_types


def _update_builds_actions():
    actions = BuildAction.objects.all()

    for action in actions:
        if action.action_type == "subassemblychange":
            action.action_type = "subchange"
        elif action.action_type == "buildadd":
            action.action_type = "add"
        elif action.action_type == "deploymenttosea":
            action.action_type = "deploymenttofield"
        elif action.action_type == "startdeploy":
            action.action_type = "startdeployment"
        action.save()
        print(action)


# Import old BuildAction objs to Action
def _import_old_build_actions():
    actions = BuildAction.objects.all()
    for action in actions:
        new_action = Action.objects.create(
            build=action.build,
            action_type=action.action_type,
            object_type="build",
            location=action.location,
            created_at=action.created_at,
            detail=action.detail,
            user=action.user,
        )


# Update legacy Build Actions if they're Deployment actions
def _update_build_dep_actions():
    builds = Build.objects.all()
    dep_action_list = [
        "startdeployment",
        "deploymentburnin",
        "deploymenttofield",
        "deploymentdetails",
        "deploymentrecover",
        "deploymentretire",
    ]
    for build in builds:
        actions = build.get_actions()
        dep_actions = actions.filter(action_type__in=dep_action_list)
        for action in dep_actions:
            action.deployment_type = "build_deployment"
            action.deployment = build.get_latest_deployment()
            action.save()
            print(action)


# Create new InventoryDeployment objects for items that are already on deployment
def _create_inv_deployments():
    builds = Build.objects.filter(is_deployed=True)
    for build in builds:
        print(build)
        for item in build.inventory.all():
            print(
                item,
                build.current_deployment(),
                build.current_deployment().deployment_start_date,
            )
            # Create InventoryDeployment record
            inventory_deployment = InventoryDeployment.objects.create(
                deployment=build.current_deployment(),
                inventory=item,
                deployment_start_date=build.current_deployment().deployment_start_date,
                deployment_burnin_date=build.current_deployment().deployment_burnin_date,
                deployment_to_field_date=build.current_deployment().deployment_to_field_date,
                deployment_recovery_date=build.current_deployment().deployment_recovery_date,
                current_status=build.current_deployment().current_status,
            )
            print(inventory_deployment, inventory_deployment.current_status)

# If Vessels are found without VesselEvents, generate and associate VesselEvents with each
def _update_vessel_events():
    for vessel in Vessel.objects.all():
        if not hasattr(vessel, "vessel_event"):
            print("adding vessel event")
            new_vessel_event = VesselEvent.objects.create(vessel=vessel)
            new_vessel_event.save()