from django.db import models
from django.utils import timezone

from roundabout.users.models import *

"""
Model to track users and registrations of "in the field" RDB instances.
These are instances that run strictly locally without internet access necessary.
"""

class FieldInstance(models.Model):
    name = models.CharField(max_length=255, null=False, blank=True, db_index=True)
    start_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    users = models.ManyToManyField('users.User', related_name='field_instances', blank=False)
    cruise = models.ForeignKey('cruises.Cruise', related_name='field_instances',
                               on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    # True if this RDB instance is registered as a FieldInstance
    is_this_instance = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    """
    # Custom save method to deactive non-deployed users
    def save(self, *args, **kwargs):
        super(FieldInstance, self).save(*args, **kwargs)
        print(self.cruise)
        if self.is_this_instance:
            for user in self.users.all():
                print(user)
                user.is_active = True
                user.save()

            users_deactivate = User.objects.exclude(id__in=self.users.all())
            for user in users_deactivate:
                print(user)
                user.is_active = False
                user.save()
    """
