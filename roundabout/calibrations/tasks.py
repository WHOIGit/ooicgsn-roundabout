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

from celery import shared_task

from roundabout.calibrations.models import CalibrationEvent, CoefficientNameEvent
from roundabout.configs_constants.models import ConfigEvent, ConfigDefaultEvent, ConstDefaultEvent

# Delete empty Events
@shared_task(bind = True)
def check_events(self):
    for event in CalibrationEvent.objects.all():
        if not event.coefficient_value_sets.exists():
            event.delete()
    for event in ConfigEvent.objects.all():
        if not event.config_values.exists():
            event.delete()
    for event in ConfigDefaultEvent.objects.all():
        if not event.config_defaults.exists():
            event.delete()
    for event in ConstDefaultEvent.objects.all():
        if not event.constant_defaults.exists():
            event.delete()
    for event in CoefficientNameEvent.objects.all():
        if not event.coefficient_names.exists():
            event.delete()