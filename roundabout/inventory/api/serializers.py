from rest_framework import serializers

from ..models import Inventory
from roundabout.locations.api.serializers import LocationSerializer
from roundabout.parts.api.serializers import PartSerializer


class InventorySerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    part = PartSerializer(read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'serial_number', 'part', 'location', ]

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary prefetching of data. """
        queryset = queryset.select_related('location').select_related('part')

        return queryset 
