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

def handle_reviewers(form):
    if form.instance.user_approver.exists():
        if form.cleaned_data['user_draft'].exists():
            if form.instance.user_draft.exists():
                model_revs = form.instance.user_draft.all()
                form_revs = form.cleaned_data['user_draft'].all()
                for user in model_revs:
                    if user not in form_revs:
                        form.instance.user_draft.remove(user)
            approvers = form.instance.user_approver.all()
            reviewers = form.cleaned_data['user_draft']
            for user in approvers:
                if user in reviewers:
                    form.instance.user_approver.remove(user)
                if user not in reviewers:
                    form.instance.user_draft.add(user)
                    form.instance.user_approver.remove(user)
        else:
            approvers = form.instance.user_approver.all()
            for user in approvers:
                form.instance.user_draft.add(user)
                form.instance.user_approver.remove(user)
    else:
        if form.cleaned_data['user_draft'].exists():
            if form.instance.user_draft.exists():
                model_revs = form.instance.user_draft.all()
                form_revs = form.cleaned_data['user_draft'].all()
                for user in model_revs:
                    if user not in form_revs:
                        form.instance.user_draft.remove(user)

            reviewers = form.cleaned_data['user_draft']
            for user in reviewers:
                form.instance.user_draft.add(user)


def user_ccc_reviews(event, user):
    found_cal_events = False
    found_conf_events = False
    found_deploy_events = False
    all_reviewed = False
    if hasattr(event,'inventory'):
        if user.calibration_events_drafter.exists():
            found_cal_events = event.inventory.calibration_events.filter(user_draft__in=[user])
        if user.config_events_reviewer.exists():
            found_conf_events = event.inventory.config_events.filter(user_draft__in=[user])
        if not found_cal_events and not found_conf_events:
            all_reviewed = True
    if hasattr(event,'part'):
        if user.reviewer_coefficientnameevents.exists():
            found_cal_events = event.part.part_coefficientnameevents.filter(user_draft__in=[user])
        if user.reviewer_confignameevents.exists():
            found_conf_events = event.part.part_confignameevents.filter(user_draft__in=[user])
        if not found_cal_events and not found_conf_events:
            all_reviewed = True
    if hasattr(event,'assembly_part'):
        if user.reviewer_configdefaultevents.exists():
            found_conf_events = event.assembly_part.assemblypart_configdefaultevents.filter(user_draft__in=[user])
        if not found_conf_events:
            all_reviewed = True
    if hasattr(event,'build'):
        if user.deployments_reviewer.exists():
            found_deploy_events = event.build.deployments.filter(user_draft__in=[user])
        if not found_deploy_events:
            all_reviewed = True
    return all_reviewed


def reviewer_users():
    reviewers = User.objects.filter(groups__name__in = ['admin','technician']).order_by('username').distinct()
    return reviewers
