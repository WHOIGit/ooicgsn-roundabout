from django.db import models

class InventoryDeploymentQuerySet(models.QuerySet):
    def get_active_deployment(self):
        return self.exclude(current_status='deploymentretire').first()
