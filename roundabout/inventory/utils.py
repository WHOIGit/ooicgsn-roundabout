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
from roundabout.ooi_ci_tools.models import BulkUploadEvent

# Get the app label names from the core utility functions
from roundabout.core.utils import set_app_labels

labels = set_app_labels()

# Utility functions for use with Inventory models
# ------------------------------------------------------------------------------

# Function to handle creating new Action records with meta data for different Action.OBJECT_TYPES
# Current objects available = Inventory, Build
def _create_action_history(
    obj,
    action_type,
    user,
    referring_obj=None,
    referring_action="",
    action_date=None,
    dep_obj=None,
    data=None,
    filename=None,
):
    # Set default variables
    object_type = obj._meta.model_name
    detail = ""
    deployment = None
    if not action_date:
        action_date = timezone.now()

    if (
        object_type == Action.BUILD
        or object_type == Action.INVENTORY
        or object_type == Action.CALEVENT
        or object_type == Action.CONSTDEFEVENT
        or object_type == Action.CONFEVENT
        or object_type == Action.CONFDEFEVENT
        or object_type == Action.COEFFNAMEEVENT
        or object_type == Action.CONFNAMEEVENT
        or object_type == Action.REFDESEVENT
        or object_type == Action.BULKUPLOAD
        or object_type == Action.CRUISEEVENT
        or object_type == Action.VESSELEVENT
    ) and not referring_obj:
        detail = obj.detail

    # create primary Action record
    action_record = Action()
    action_record.action_type = action_type
    action_record.object_type = object_type
    action_record.user = user
    if hasattr(obj, "location"):
        action_record.location = obj.location
    action_record.detail = detail
    action_record.created_at = action_date
    if data:
        action_record.data = data

    # set deployment_type by checking if a Build object started the action
    if isinstance(obj, Build) or isinstance(referring_obj, Build):
        deployment_type = Action.BUILD_DEPLOYMENT
    else:
        deployment_type = Action.INVENTORY_DEPLOYMENT

    # set the primary object this record refers to
    if object_type == Action.BUILD:
        obj_label = labels["label_builds_app_singular"]
        action_record.build = obj
        if dep_obj:
            deployment = dep_obj
            obj_label = "Deployment"
            detail = dep_obj.deployment_number
        else:
            deployment = obj.current_deployment()
        # Set extra meta data fields
        action_record.deployment = deployment

    elif object_type == Action.INVENTORY:
        obj_label = labels["label_inventory_app_singular"]
        action_record.inventory = obj
        action_record.parent = obj.parent

        if obj.build:
            deployment = obj.build.current_deployment()
        # Set extra meta data fields
        action_record.build = obj.build
        action_record.deployment = deployment

    elif object_type == Action.CALEVENT:
        obj_label = "Calibration Event"
        action_record.calibration_event = obj

    elif object_type == Action.CONSTDEFEVENT:
        obj_label = "Constant Default Event"
        action_record.const_default_event = obj

    elif object_type == Action.CONFEVENT:
        obj_label = "Configuration Event"
        action_record.config_event = obj

    elif object_type == Action.CONFDEFEVENT:
        obj_label = "Configuration Default Event"
        action_record.config_default_event = obj

    elif object_type == Action.COEFFNAMEEVENT:
        obj_label = "Calibration(s)"
        action_record.coefficient_name_event = obj

    elif object_type == Action.CONFNAMEEVENT:
        obj_label = "Configuration(s)"
        action_record.config_name_event = obj

    elif object_type == Action.LOCATION:
        obj_label = "Location"
        action_record.location = obj
        action_record.location_parent = obj.parent

    elif object_type == Action.CRUISE:
        obj_label = "Cruise"
        action_record.cruise = obj

    elif object_type == Action.VESSEL:
        obj_label = "Vessel"
        action_record.vessel = obj

    elif object_type == Action.DEPLOYMENT:
        obj_label = "Deployment"
        action_record.deployment = obj
        action_record.build = obj.build

    elif object_type == Action.REFDESEVENT:
        obj_label = "Reference Designator"
        action_record.reference_designator_event = obj

    elif object_type == Action.BULKUPLOAD:
        obj_label = "Bulk Upload"
        action_record.bulk_upload_event = obj

    elif object_type == Action.CRUISEEVENT:
        obj_label = "Cruise Event"
        action_record.cruise_event = obj

    elif object_type == Action.VESSELEVENT:
        obj_label = "Vessel Event"
        action_record.vessel_event = obj

    # Run through the discrete Actions, set up details text and extra records if needed.
    if action_type == Action.ADD:
        action_record.detail = "%s first added to RDB. %s" % (obj_label, detail)
        action_record.save()

    elif action_type == Action.UPDATE:
        if object_type == Action.BULKUPLOAD:
            if filename:
                action_record.detail = "%s details updated. (%s)" % (
                    obj_label,
                    filename,
                )
        else:
            action_record.detail = "%s details updated." % (obj_label)
        if object_type == Action.CALEVENT:
            pass
        elif object_type == Action.CONFEVENT:
            pass
        elif object_type == Action.DEPLOYMENT:
            pass
        action_record.save()

    elif action_type == Action.LOCATIONCHANGE or action_type == Action.MOVETOTRASH:
        action_record.detail = "Moved to %s from %s. %s" % (
            obj.location,
            obj.actions.latest().location,
            detail,
        )
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
                    action_record.detail = "Sub-%s %s removed." % (
                        labels["label_assemblies_app_singular"],
                        referring_obj,
                    )
                else:
                    action_record.detail = "Sub-%s %s added." % (
                        labels["label_assemblies_app_singular"],
                        referring_obj,
                    )
            else:
                if referring_action == Action.ADDTOBUILD:
                    action_record.detail = "Sub-%s %s added." % (
                        labels["label_assemblies_app_singular"],
                        referring_obj,
                    )
                else:
                    action_record.detail = "Sub-%s %s removed." % (
                        labels["label_assemblies_app_singular"],
                        referring_obj,
                    )
        else:
            if obj.parent:
                action_record.detail = "Added to %s." % (obj.parent)
            else:
                action_record.detail = "Removed from %s." % (obj.get_latest_parent())
                _create_action_history(
                    obj.get_latest_parent(), Action.SUBCHANGE, user, obj
                )
        action_record.save()

    elif action_type == Action.ADDTOBUILD:
        if obj.location_changed():
            _create_action_history(
                obj, Action.LOCATIONCHANGE, user, "", "", action_date
            )

        action_record.detail = "Moved to %s." % (obj.build)
        action_record.save()

        if not referring_obj:
            if obj.parent:
                _create_action_history(obj, Action.SUBCHANGE, user, "", "", action_date)
                _create_action_history(
                    obj.parent, Action.SUBCHANGE, user, obj, "", action_date
                )

        # If Build is deployed, need to add extra Action record to add to Deployment
        if obj.build.is_deployed:
            _create_action_history(
                obj, Action.STARTDEPLOYMENT, user, "", "", action_date
            )
            if obj.build.current_deployment().current_status == Action.DEPLOYMENTBURNIN:
                _create_action_history(
                    obj, Action.DEPLOYMENTBURNIN, user, "", "", action_date
                )

        # Add Action record for the Build
        _create_action_history(
            obj.get_latest_build(),
            Action.SUBCHANGE,
            user,
            obj,
            action_type,
            action_date,
        )

    elif action_type == Action.REMOVEFROMBUILD:
        if obj.location_changed():
            _create_action_history(
                obj, Action.LOCATIONCHANGE, user, "", "", action_date
            )

        if not obj.get_latest_build():
            print(
                f"ERROR REMOVING {obj} FROM BUILD. NO BUILD IN ACTION HISTORY, POSSIBLE BROKEN TREE"
            )
            print("REFRESH INVENTORY MPTT TREE...")
            Inventory.objects.rebuild()
            print("REBUILD COMPLETE")

        action_record.detail = "Removed from %s. %s" % (obj.get_latest_build(), detail)
        action_record.location = obj.get_latest_build().location
        action_record.save()

        if not referring_obj and obj.parent_changed():
            _create_action_history(obj, Action.SUBCHANGE, user)
            _create_action_history(obj.get_latest_parent(), Action.SUBCHANGE, user, obj)

        # If Build is deployed, need to add extra Action record to add to Deployment
        if obj.get_latest_build().is_deployed:
            _create_action_history(
                obj, Action.DEPLOYMENTRETIRE, user, "", "", action_date
            )

        # Add Action record for the Build
        _create_action_history(
            obj.get_latest_build(),
            Action.SUBCHANGE,
            user,
            obj,
            action_type,
            action_date,
        )

    elif action_type == Action.ASSIGNDEST:
        action_record.detail = "Destination assigned - %s." % (
            obj.assembly_part.assembly_revision
        )
        action_record.save()

    elif action_type == Action.REMOVEDEST:
        action_record.detail = "Destination Assignment removed. %s" % (detail)
        action_record.save()

    elif action_type == Action.TEST:
        test_result = obj.test_results.latest()

        action_record.detail = "Test Result - %s: %s. %s" % (
            test_result.inventory_test.name,
            test_result.get_result_display(),
            test_result.notes,
        )
        action_record.save()

    elif action_type == Action.STARTDEPLOYMENT:
        if obj.location_changed():
            _create_action_history(
                obj, Action.LOCATIONCHANGE, user, "", "", action_date
            )

        action_record.detail = "%s %s started." % (
            labels["label_deployments_app_singular"],
            deployment,
        )
        action_record.deployment_type = deployment_type
        if deployment_type == Action.BUILD_DEPLOYMENT:
            action_record.created_at = deployment.deployment_start_date

        if isinstance(obj, Inventory):
            # Create InventoryDeployment record
            inventory_deployment = InventoryDeployment.objects.create(
                deployment=deployment,
                inventory=obj,
                assembly_part=obj.assembly_part,
                deployment_start_date=action_date,
            )
            action_record.inventory_deployment = inventory_deployment
        action_record.save()

    elif action_type == Action.DEPLOYMENTBURNIN:
        if obj.location_changed():
            _create_action_history(
                obj, Action.LOCATIONCHANGE, user, "", "", action_date
            )

        action_record.detail = "%s %s burn in." % (
            labels["label_deployments_app_singular"],
            deployment,
        )
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
            _create_action_history(
                obj, Action.LOCATIONCHANGE, user, "", "", action_date
            )

        action_record.detail = "Deployed to field on %s." % (deployment)
        action_record.created_at = deployment.deployment_to_field_date
        action_record.deployment_type = deployment_type
        action_record.latitude = deployment.latitude
        action_record.longitude = deployment.longitude
        action_record.depth = deployment.depth

        if isinstance(obj, Build):
            action_record.cruise = deployment.cruise_deployed
            action_record.detail = "%s Cruise: %s" % (
                action_record.detail,
                deployment.cruise_deployed,
            )

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
            action_record.detail = "%s Cruise: %s" % (
                action_record.detail,
                inventory_deployment.cruise_deployed,
            )
        action_record.save()

    elif action_type == Action.DEPLOYMENTRECOVER:
        if obj.location_changed():
            _create_action_history(
                obj, Action.LOCATIONCHANGE, user, "", "", action_date
            )

        deployment = obj.get_latest_deployment()
        action_record.detail = "Recovered from %s. %s" % (deployment, detail)
        action_record.deployment_type = deployment_type
        action_record.deployment = deployment

        if isinstance(obj, Build):
            action_record.cruise = deployment.cruise_recovered
            action_record.detail = "%s Cruise: %s" % (
                action_record.detail,
                deployment.cruise_recovered,
            )

        # Update InventoryDeployment record
        if isinstance(obj, Inventory):
            inventory_deployment = obj.inventory_deployments.get_active_deployment()
            # Only update date/cruise on full Build deployment, not individual item
            if deployment_type == Action.BUILD_DEPLOYMENT:
                inventory_deployment.deployment_recovery_date = action_date
                if deployment:
                    inventory_deployment.cruise_recovered = deployment.cruise_recovered
            inventory_deployment.save()
            action_record.inventory_deployment = inventory_deployment
            action_record.build = obj.get_latest_build()
            action_record.detail = "Recovered from %s. %s" % (deployment, detail)
            action_record.created_at = action_date
            action_record.cruise = inventory_deployment.cruise_recovered
            action_record.detail = "%s Cruise: %s" % (
                action_record.detail,
                inventory_deployment.cruise_recovered,
            )

        action_record.save()
        # Run secondary Action records after completion
        if deployment_type == Action.INVENTORY_DEPLOYMENT:
            # Add Remove from Build record
            _create_action_history(
                obj, Action.REMOVEFROMBUILD, user, "", "", action_date
            )

    elif action_type == Action.DEPLOYMENTRETIRE:
        deployment = obj.get_latest_deployment()
        action_record.deployment = deployment
        action_record.detail = "%s %s ended for this %s." % (
            labels["label_deployments_app_singular"],
            deployment,
            obj_label,
        )
        # update InventoryDeployment record
        if isinstance(obj, Inventory):
            inventory_deployment = obj.inventory_deployments.get_active_deployment()
            if inventory_deployment:
                inventory_deployment.deployment_retire_date = action_date
                inventory_deployment.save()
                action_record.inventory_deployment = inventory_deployment
        action_record.save()

    elif action_type == Action.REVIEWAPPROVE:
        action_record.detail = "Reviewer approved %s %s" % (obj_label, detail)
        action_record.save()

    elif action_type == Action.EVENTAPPROVE:
        action_record.detail = "%s Approved %s" % (obj_label, detail)
        action_record.save()

    elif action_type == Action.CALCSVIMPORT:
        action_record.detail = "%s Created via CSV Import. %s" % (obj_label, detail)
        action_record.save()
    elif action_type == Action.CALCSVUPDATE:
        action_record.detail = "%s Updated via CSV Import %s" % (obj_label, detail)
        action_record.save()
    else:
        action_record.save()

    return action_record


# Return inventory/part/assembly-part item id's where logged-in user is a CCC-reviewer
def logged_user_review_items(logged_user, template_type):
    full_list = []
    inv_id_from_bulk_events = []
    part_id_from_bulk_events = []
    try:
        bulk_event = BulkUploadEvent.objects.get(pk=1)
    except BulkUploadEvent.DoesNotExist:
        bulk_event = None
    if bulk_event:
        if logged_user in bulk_event.user_draft.all():
            inv_id_from_bulk_events = [
                inv_id["id"] for inv_id in bulk_event.inventory.values("id")
            ]
            part_id_from_bulk_events = [
                inv_id["id"] for inv_id in bulk_event.parts.values("id")
            ]
    if template_type == "inv":
        inv_id_from_cal_events = [
            inv_id["inventory_id"]
            for inv_id in logged_user.reviewer_calibrationevents.values("inventory_id")
        ]
        inv_id_from_config_events = [
            inv_id["inventory_id"]
            for inv_id in logged_user.reviewer_configevents.values("inventory_id")
        ]
        inv_id_from_const_def_events = [
            inv_id["inventory_id"]
            for inv_id in logged_user.reviewer_constdefaultevents.values("inventory_id")
        ]
        build_id_from_dep_events = [
            build_id["build_id"]
            for build_id in logged_user.reviewer_deployments.values("build_id")
        ]
        full_inv_list = set(
            inv_id_from_cal_events
            + inv_id_from_config_events
            + inv_id_from_const_def_events
            + inv_id_from_bulk_events
            + build_id_from_dep_events
        )
        full_list = list(full_inv_list)

    if template_type == "part":
        parts_from_config_name_events = [
            part_id["part_id"]
            for part_id in logged_user.reviewer_confignameevents.values("part_id")
        ]
        parts_from_cal_name_events = [
            part_id["part_id"]
            for part_id in logged_user.reviewer_coefficientnameevents.values("part_id")
        ]
        full_part_list = set(
            parts_from_config_name_events
            + parts_from_cal_name_events
            + part_id_from_bulk_events
        )
        full_list = list(full_part_list)

    if template_type == "assm":
        assmparts_from_config_def_events = [
            part_id["assembly_part__part_id"]
            for part_id in logged_user.reviewer_configdefaultevents.values(
                "assembly_part__part_id"
            )
        ]
        assmparts_from_refdes_events = [
            part_id["assembly_part__part_id"]
            for part_id in logged_user.reviewer_referencedesignatorevents.values(
                "assembly_part__part_id"
            )
        ]
        full_assm_list = set(
            assmparts_from_config_def_events + assmparts_from_refdes_events
        )
        full_list = list(full_assm_list)

    if template_type == "cruise":
        cruises_from_cruise_events = [
            cruise_id["cruise_id"]
            for cruise_id in logged_user.reviewer_cruiseevents.values("cruise_id")
        ]
        full_cruise_list = set(cruises_from_cruise_events)
        full_list = list(full_cruise_list)

    return full_list
