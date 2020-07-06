from django.db import models

class InventoryDeploymentQuerySet(models.QuerySet):
    def get_active_deployment(self):
        return self.exclude(current_status='deploymentretire').first()


class ActionQuerySet(models.QuerySet):
    def get_latest_set(self):
        return self.order_by('action_type', '-created_at').distinct('action_type')

    def get_latest_all(self, object_type):
        # object_type is one of Action.OBJECT_TYPES from Action model
        if (any(object_type in item for item in self.model.OBJECT_TYPES)): 
            return self.order_by(object_type, '-created_at').distinct(object_type)
        return self
