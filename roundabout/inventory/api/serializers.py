from rest_framework import serializers

from ..models import Inventory
from roundabout.locations.api.serializers import LocationSerializer


class InventorySerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'serial_number', 'part', 'location', ]
