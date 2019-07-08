from django.db import models
from mptt.models import TreeForeignKey
from django.utils import timezone
from model_utils import FieldTracker

from roundabout.locations.models import Location
from roundabout.assemblies.models import Assembly
from roundabout.users.models import User

# Build model

class Build(models.Model):
    build_number = models.CharField(max_length=255, unique=False)
    location = TreeForeignKey(Location, related_name='builds',
                              on_delete=models.SET_NULL, null=True, blank=False)
    assembly = models.ForeignKey(Assembly, related_name='builds',
                             on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    build_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    detail = models.TextField(blank=True)
    is_deployed = models.BooleanField(default=False)

    tracker = FieldTracker(fields=['location',])

    class Meta:
        ordering = ['assembly', 'build_number']

    def __str__(self):
        return '%s - %s' % (self.build_number, self.assembly.name)

    def current_deployment(self):
        # set default to None
        current_deployment = None

        if self.is_deployed:
            # get the latest deployment if available
            current_deployment = self.deployments.first()
        return current_deployment

    def current_deployment_status(self):
        # set default deployment_status to None
        deployment_status = None

        # get the latest deployment if available
        latest_deployment = self.deployments.first()
        if latest_deployment:
            deployment_action = latest_deployment.deployment_action.first()
            if deployment_action.action_type != 'retire':
                deployment_status = deployment_action.action_type
            else:
                deployment_status = None
        return deployment_status


class BuildAction(models.Model):
    BUILDADD = 'buildadd'
    LOCATIONCHANGE = 'locationchange'
    SUBASSEMBLYCHANGE = 'subassemblychange'
    STARTDEPLOY = 'startdeploy'
    REMOVEFROMDEPLOYMENT = 'removefromdeployment'
    DEPLOYMENTBURNIN = 'deploymentburnin'
    DEPLOYMENTTOSEA = 'deploymenttosea'
    DEPLOYMENTRECOVER = 'deploymentrecover'
    TEST = 'test'
    NOTE = 'note'
    HISTORYNOTE = 'historynote'
    TICKET = 'ticket'
    FLAG = 'flag'
    MOVETOTRASH = 'movetotrash'
    ACT_TYPES = (
        (BUILDADD, 'Add Build'),
        (LOCATIONCHANGE, 'Location Change'),
        (SUBASSEMBLYCHANGE, 'Subassembly Change'),
        (STARTDEPLOY, 'Start Deployment'),
        (REMOVEFROMDEPLOYMENT, 'Remove from Deployment'),
        (DEPLOYMENTBURNIN, 'Deployment Burnin'),
        (DEPLOYMENTTOSEA, 'Deployment to Sea'),
        (DEPLOYMENTRECOVER, 'Deployment Recovered'),
        (TEST, 'Test'),
        (NOTE, 'Note'),
        (HISTORYNOTE, 'Historical Note'),
        (TICKET, 'Work Ticket'),
        (FLAG, 'Flag'),
        (MOVETOTRASH, 'Move to Trash'),
    )
    action_type = models.CharField(max_length=20, choices=ACT_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    detail = models.TextField(blank=True)
    user = models.ForeignKey(User, related_name='actions',
                             on_delete=models.SET_NULL, null=True, blank=False)
    location = TreeForeignKey(Location, related_name='actions',
                              on_delete=models.SET_NULL, null=True, blank=False)
    build = models.ForeignKey(Build, related_name='actions',
                                 on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at', 'action_type']

    def __str__(self):
        return self.get_action_type_display()
