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

from django import template
import datetime

from roundabout.inventory.models import Inventory, Action, Deployment
from roundabout.locations.models import Location
from roundabout.parts.models import Part
from roundabout.userdefinedfields.models import Field, FieldValue

register = template.Library()

# Return tomorrow's date for Deployment maxDate validation
@register.simple_tag
def tomorrow(format):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    return tomorrow.strftime(format)



@register.simple_tag
def user_is_deploy_reviewer(build,logged_user):
    if build:
        if build.deployments.exists():
            if logged_user.reviewer_deployments.exists():
                found_events = build.deployments.filter(user_draft__in=[logged_user])
                if found_events:
                    return True
    return False