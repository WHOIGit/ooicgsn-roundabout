from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from roundabout.inventory.models import Action
from roundabout.users.models import User


# Comment model
class Comment(models.Model):
    class Meta:
        ordering = ['-created_at']
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


# class CommentNode(MPTTModel):
#     class MPTTMeta:
#         order_insertion_by = ['-created_at']
#     def __str__(self):
#         return self.detail
#     def get_object_type(self):
#         return 'comment_node'
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     parent = TreeForeignKey('self', related_name='children', on_delete=models.CASCADE, null=True, blank=True, db_index=True)
#     action = models.ForeignKey(Action, related_name='comment_nodes', on_delete=models.CASCADE, null=True)
#     user = models.ForeignKey(User, related_name='comment_nodes', on_delete=models.SET_NULL, null=True)
#     detail = models.TextField(blank=True)