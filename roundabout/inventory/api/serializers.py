from ..models import Inventory
from rest_framework import serializers

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ('id', 'serial_number', 'part', 'location', )
