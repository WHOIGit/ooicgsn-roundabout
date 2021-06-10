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
from django.utils import timezone

from roundabout.assemblies.models import AssemblyPart
from roundabout.inventory.models import Inventory, Deployment, DeploymentAction, Action
from roundabout.parts.models import Part
from roundabout.users.models import User
from roundabout.ooi_ci_tools.models import CCCEvent


# Tracks Configuration and Constant event history across Inventory Parts
class ConfigEvent(CCCEvent):
    class Meta:
        ordering = ['-configuration_date']
    def __str__(self):
        return self.configuration_date.strftime("%m/%d/%Y")
    def get_object_type(self):
        return 'config_event'
    CONFIG_TYPE = (
        ("cnst", "Constant"),
        ("conf", "Configuration"),
    )
    configuration_date = models.DateTimeField(default=timezone.now)
    config_type = models.CharField(max_length=4, choices=CONFIG_TYPE, null=False, blank=False, default="cnst")

    def get_actions(self):
        return self.actions.filter(object_type=Action.CONFEVENT)

    def get_latest_deployment_date(self):
        if self.deployment:
            if self.deployment.deployment_to_field_date:
                return self.deployment.deployment_to_field_date.strftime("%m/%d/%Y")
        return 'TBD'

class ConfigEventHyperlink(models.Model):
    text = models.CharField(max_length=255, unique=False, blank=False, null=False)
    url = models.URLField(max_length=1000)
    parent = models.ForeignKey(ConfigEvent, related_name='hyperlinks',
                 on_delete=models.CASCADE, null=False, blank=False)

    class Meta: ordering = ['text']
    def __str__(self): return self.text

# Tracks Config Name  history across Parts
class ConfigNameEvent(CCCEvent):
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.created_at.strftime("%m/%d/%Y")
    def get_object_type(self):
        return 'config_name_event'

    def get_actions(self):
        return self.actions.filter(object_type='confignameevent')

# Tracks Configurations across Parts
class ConfigName(models.Model):
    class Meta:
        ordering = ['created_at']
        unique_together = ['part','config_type','name']
    def __str__(self):
        return self.name
    def get_object_type(self):
        return 'config_name'
    CONFIG_TYPE = (
        ("cnst", "Constant"),
        ("conf", "Configuration"),
    )
    name = models.CharField(max_length=255, unique=False, db_index=True)
    config_type = models.CharField(max_length=4, choices=CONFIG_TYPE, null=False, blank=False, default="cnst")
    created_at = models.DateTimeField(default=timezone.now)
    deprecated = models.BooleanField(null=False, default=False)
    part = models.ForeignKey(Part, related_name='config_names', on_delete=models.CASCADE, null=True)
    include_with_calibrations = models.BooleanField(null=False, default=False)
    config_name_event = models.ForeignKey(ConfigNameEvent, related_name='config_names', on_delete=models.CASCADE, null=True)

# Tracks Configuration/Constant Sets across ConfigNames
class ConfigValue(models.Model):
    class Meta:
        ordering = ['created_at']
        unique_together = ['config_event','config_name']
    def __str__(self):
        return self.config_value
    def get_object_type(self):
        return 'config_value'
    config_value = models.CharField(max_length=255, unique=False, db_index=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    config_name = models.ForeignKey(ConfigName, related_name='config_values', on_delete=models.CASCADE, null=True)
    config_event = models.ForeignKey(ConfigEvent, related_name='config_values', on_delete=models.CASCADE, null=True)
    def config_value_with_export_formatting(self):
        if ',' in self.config_value:
            return '[{}]'.format(self.config_value)
        else:
            return self.config_value


# Tracks Constant Default event history across Inventory Parts
class ConstDefaultEvent(CCCEvent):
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.created_at.strftime("%m/%d/%Y")
    def get_object_type(self):
        return 'constant_default_event'

    def get_actions(self):
        return self.actions.filter(object_type=Action.CONSTDEFEVENT)


# Tracks Constant Defaults across ConstDefaultEvents
class ConstDefault(models.Model):
    class Meta:
        ordering = ['created_at']
        unique_together = ['const_event','config_name']
    def __str__(self):
        return self.default_value
    def get_object_type(self):
        return 'constant_default'
    default_value = models.CharField(max_length=255, unique=False, db_index=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    config_name = models.ForeignKey(ConfigName, related_name='constant_defaults', on_delete=models.CASCADE, null=True)
    const_event = models.ForeignKey(ConstDefaultEvent, related_name='constant_defaults', on_delete=models.CASCADE, null=True)


# Tracks Config Default Event history across Assembly Parts
class ConfigDefaultEvent(CCCEvent):
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.created_at.strftime("%m/%d/%Y")
    def get_object_type(self):
        return 'config_default_event'

    def get_actions(self):
        return self.actions.filter(object_type='configdefaultevent')


# Tracks Config Defaults across ConstDefaultEvents
class ConfigDefault(models.Model):
    class Meta:
        ordering = ['created_at']
        unique_together = ['conf_def_event','config_name']
    def __str__(self):
        return self.default_value
    def get_object_type(self):
        return 'config_default'
    default_value = models.CharField(max_length=255, unique=False, db_index=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    config_name = models.ForeignKey(ConfigName, related_name='config_defaults', on_delete=models.CASCADE, null=True)
    conf_def_event = models.ForeignKey(ConfigDefaultEvent, related_name='config_defaults', on_delete=models.CASCADE, null=True)
