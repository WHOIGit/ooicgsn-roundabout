# Mixins to use across all API code
from rest_framework import viewsets
from roundabout.inventory.utils import _create_action_history
from roundabout.inventory.models import Action

# automatically add Action History record if object added/updated
class AddActionHistoryMixin(viewsets.ModelViewSet):
    def save_with_action_history(self, serializer, action_type, action_date=None):
        print(serializer.validated_data)
        obj = serializer.save()
        _create_action_history(
            obj,
            action_type,
            self.request.user,
            action_date=action_date,
        )

    def perform_create(self, serializer):
        action_date = serializer.validated_data.get("created_at", None)
        self.save_with_action_history(serializer, Action.ADD, action_date)

    def perform_update(self, serializer):
        self.save_with_action_history(serializer, Action.UPDATE)
