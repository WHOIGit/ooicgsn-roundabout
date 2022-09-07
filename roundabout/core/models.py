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

from django.db import models


class CoreConfig(models.Model):
    """
    Model to hold general global settings, allows user to manage settings through web app
    """

    RESET_TESTS_ON_DEPLOYMENT_END = "reset_tests_on_deployment_end"
    CONFIG_TYPES = ((RESET_TESTS_ON_DEPLOYMENT_END, "Reset Tests on Deployment End"),)

    name = models.CharField(max_length=200, choices=CONFIG_TYPES)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
