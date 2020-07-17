from django.db import models
from django.core.validators import MinValueValidator, DecimalValidator, MaxValueValidator, RegexValidator, MaxLengthValidator
from django.utils import timezone
from roundabout.parts.models import Part
from roundabout.inventory.models import Inventory, Deployment, DeploymentAction, Action
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
    user_draft = models.ManyToManyField(User, related_name='config_events_reviewer')
    user_approver = models.ManyToManyField(User, related_name='config_events_approver')
    inventory = models.ForeignKey(Inventory, related_name='config_events', on_delete=models.CASCADE, null=False)
    deployment = models.ForeignKey(Deployment, related_name='config_events', on_delete=models.CASCADE, null=True)
    approved = models.BooleanField(choices=APPROVAL_STATUS, blank=False, default=False)
    detail = models.TextField(blank=True)

    def get_actions(self):
        return self.actions.filter(object_type=Action.CONFEVENT)

    def get_latest_deployment_date(self):
        deploy_record = self.deployment.build.actions.filter(action_type=Action.DEPLOYMENTTOFIELD).first()
        if deploy_record:
            return deploy_record.created_at.strftime("%m/%d/%Y")
        else:
            return 'TBD'

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
    config_type = models.CharField(max_length=4, choices=CONFIG_TYPE, null=False, blank=False, default="cnst")
    created_at = models.DateTimeField(default=timezone.now)
    part = models.ForeignKey(Part, related_name='config_names', on_delete=models.CASCADE, null=True)

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


# Tracks Constant Default event history across Inventory Parts
class ConstDefaultEvent(models.Model):
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.created_at.strftime("%m/%d/%Y")
    def get_object_type(self):
        return 'constant_default_event'
    APPROVAL_STATUS = (
        (True, "Approved"),
        (False, "Draft"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_draft = models.ManyToManyField(User, related_name='constant_default_events_reviewer')
    user_approver = models.ManyToManyField(User, related_name='constant_default_events_approver')
    inventory = models.ForeignKey(Inventory, related_name='constant_default_events', on_delete=models.CASCADE, null=False)
    approved = models.BooleanField(choices=APPROVAL_STATUS, blank=False, default=False)
    detail = models.TextField(blank=True)
    
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