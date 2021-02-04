from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from roundabout.inventory.models import Action
from roundabout.users.models import User


# Comment model
class Comment(models.Model):
    class Meta:
        ordering = ['created_at']
    def __str__(self):
        return self.detail
    def get_object_type(self):
        return 'comment'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', related_name = 'comments', on_delete=models.CASCADE, null=True)
    action = models.ForeignKey(Action, related_name='comments', on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, related_name='comments', on_delete=models.SET_NULL, null=True)
    detail = models.TextField(blank=True)