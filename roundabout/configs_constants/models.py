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
from django.core.validators import MinValueValidator, DecimalValidator, MaxValueValidator, RegexValidator, MaxLengthValidator
from django.utils import timezone
from roundabout.parts.models import Part
from roundabout.inventory.models import Inventory, Deployment, DeploymentAction
from roundabout.users.models import User
from decimal import Decimal
from sigfig import round
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Tracks Configuration and Constant event history across Inventory Parts
class ConfigEvent(models.Model):
    class Meta:
        ordering = ['-configuration_date']
    def __str__(self):
        return self.configuration_date
    def get_object_type(self):
        return 'config_event'
    APPROVAL_STATUS = (
        (True, "Approved"),
        (False, "Draft"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    configuration_date = models.DateTimeField(default=timezone.now)
    user_draft = models.ForeignKey(User, related_name='config_events_drafter', on_delete=models.SET_NULL, null=True, blank=False)
    user_approver = models.ForeignKey(User, related_name='config_events_approver', on_delete=models.SET_NULL, null=True, blank=False)
    inventory = models.ForeignKey(Inventory, related_name='config_events', on_delete=models.CASCADE, null=False)
    deployment = models.ForeignKey(Deployment, related_name='config_events', on_delete=models.CASCADE, null=True)
    approved = models.BooleanField(choices=APPROVAL_STATUS, blank=False, default=False)

    def get_latest_deployment_date(self):
        deploy_record = DeploymentAction.objects.filter(deployment=self.deployment).filter(action_type='deploy').first()
        return deploy_record.created_at

# Tracks Configurations across Parts
class ConfigName(models.Model):
    class Meta:
        ordering = ['name']
        unique_together = ['part','name']
    def __str__(self):
        return self.name
    def get_object_type(self):
        return 'config_name'
    CONFIG_TYPE = (
        ("cnst", "Constant"),
        ("conf", "Configuration"),
    )
    name = models.CharField(max_length=255, unique=False, db_index=True)
    config_type = models.CharField(max_length=4, choices=CONFIG_TYPE, null=False, blank=False, default="ct")
    created_at = models.DateTimeField(default=timezone.now)
    part = models.ForeignKey(Part, related_name='config_names', on_delete=models.CASCADE, null=True)

# Tracks Configuration/Constant Sets across Calibrations 
class ConfigValue(models.Model):
    class Meta:
        ordering = ['created_at']
        unique_together = ['config_event','config_name']
    def __str__(self):
        return self.config_value
    def get_object_type(self):
        return 'config_value'
    config_value = models.CharField(max_length=255, unique=False, db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    config_name = models.ForeignKey(ConfigName, related_name='config_values', on_delete=models.CASCADE, null=True)
    config_event = models.ForeignKey(ConfigEvent, related_name='config_values', on_delete=models.CASCADE, null=True)