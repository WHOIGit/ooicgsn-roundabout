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

from django.db.models import Count
from sigfig import round
from statistics import mean, stdev

from roundabout.users.models import User
from roundabout.calibrations.models import CalibrationEvent, CoefficientName
from roundabout.configs_constants.models import ConfigEvent, ConfigDefaultEvent, ConstDefaultEvent
from roundabout.ooi_ci_tools.models import Threshold



# When an Event is updated, current Approvers reset to Reviewers
def handle_reviewers(instanace_draft, instance_approvers, form_draft):
    if instance_approvers.exists():
        if form_draft.exists():
            if instanace_draft.exists():
                model_revs = instanace_draft.all()
                form_revs = form_draft.all()
                for user in model_revs:
                    if user not in form_revs:
                        instanace_draft.remove(user)
            approvers = instance_approvers.all()
            reviewers = form_draft
            for user in approvers:
                if user in reviewers:
                    instance_approvers.remove(user)
                if user not in reviewers:
                    instanace_draft.add(user)
                    instance_approvers.remove(user)
        else:
            approvers = instance_approvers.all()
            for user in approvers:
                instanace_draft.add(user)
                instance_approvers.remove(user)
    else:
        if form_draft.exists():
            if instanace_draft.exists():
                model_revs = instanace_draft.all()
                form_revs = form_draft.all()
                for user in model_revs:
                    if user not in form_revs:
                        instanace_draft.remove(user)

            reviewers = form_draft
            for user in reviewers:
                instanace_draft.add(user)



# When an Event Review is Approved or Unapproved, check if the User needs to Review Events elsewhere
def user_ccc_reviews(event, user, evt_type):
    found_cal_events = False
    found_bulk_events = False
    found_conf_events = False
    found_const_events = False
    found_constdef_events = False
    found_deploy_events = False
    found_refdes_events = False
    all_reviewed = False

    # Inventory template
    if evt_type in ['calibration_event','config_event', 'constant_default_event', 'bulk_upload_event']:
        if user.reviewer_calibrationevents.exists():
            if hasattr(event.inventory,'inventory_calibrationevents'):
                found_cal_events = True if len(event.inventory.inventory_calibrationevents.filter(user_draft__in=[user])) >= 1 else False
        if user.reviewer_configevents.exists():
            if hasattr(event.inventory,'inventory_configevents'):
                found_conf_events = True if len(event.inventory.inventory_configevents.filter(user_draft__in=[user], config_type = 'conf')) >= 1 else False
                found_const_events = True if len(event.inventory.inventory_configevents.filter(user_draft__in=[user], config_type = 'cnst')) >= 1 else False
        if user.reviewer_constdefaultevents.exists():
            if hasattr(event.inventory,'inventory_constdefaultevents'):
                found_constdef_events = True if len(event.inventory.inventory_constdefaultevents.filter(user_draft__in=[user])) >= 1 else False
        if user.reviewer_bulkuploadevents.exists():
            found_bulk_events = True
        if not found_cal_events and not found_conf_events and not found_const_events and not found_constdef_events and not found_bulk_events:
            all_reviewed = True

    # Part template
    if evt_type in ['coefficient_name_event', 'config_name_event']:
        if user.reviewer_coefficientnameevents.exists():
            found_cal_events = True if len(event.part.part_coefficientnameevents.filter(user_draft__in=[user])) >= 1 else False
        if user.reviewer_confignameevents.exists():
            found_conf_events = True if len(event.part.part_confignameevents.filter(user_draft__in=[user])) >= 1 else False
        if not found_cal_events and not found_conf_events:
            all_reviewed = True

    # Assembly Template
    if evt_type in ['config_default_event', 'reference_designator_event']:
        if user.reviewer_configdefaultevents.exists():
            found_conf_events = True if len(event.assembly_part.assemblypart_configdefaultevents.filter(user_draft__in=[user])) >= 1 else False
        if user.reviewer_referencedesignatorevents.exists():
            found_refdes_events = True if len(event.assembly_part.assemblypart_referencedesignatorevents.filter(user_draft__in=[user])) >= 1 else False
        if not found_conf_events and not found_refdes_events:
            all_reviewed = True
    # Deployment template
    if evt_type in ['deployment']:
        if user.reviewer_deployments.exists():
            found_deploy_events = True if len(event.build.deployments.filter(user_draft__in=[user])) >= 1 else False
        if not found_deploy_events:
            all_reviewed = True

    # Cruise template
    if evt_type in ['cruise_event']:
        found_cruise_events = True if user in event.user_draft.all() else False
        if not found_cruise_events:
            all_reviewed = True

    # Vessel template
    if evt_type in ['vessel_event']:
        found_vessel_events = False
        if user.reviewer_vesselevents.exists():
            found_vessel_events = True if user in event.user_draft.all() else False
        if not found_vessel_events:
            all_reviewed = True
    review_obj = {
        'found_cal_events': found_cal_events,
        'found_const_events': found_const_events,
        'found_bulk_events': found_bulk_events,
        'found_conf_events': found_conf_events,
        'found_constdef_events': found_constdef_events,
        'found_deploy_events': found_deploy_events,
        'found_refdes_events': found_refdes_events,
        'all_reviewed': all_reviewed
    }
    return review_obj


# Return Users containing either Technician or Admin group permissions
def reviewer_users():
    reviewers = User.objects.filter(groups__name__in = ['admin','technician']).order_by('username').distinct()
    return reviewers
