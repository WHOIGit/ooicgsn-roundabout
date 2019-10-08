from rest_framework import serializers

from ..models import Inventory
from roundabout.locations.api.serializers import LocationSerializer
from roundabout.parts.api.serializers import PartSerializer


class InventorySerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    part = PartSerializer(read_only=True)
    custom_fields = serializers.SerializerMethodField('get_custom_fields')

    class Meta:
        model = Inventory
        fields = ['id', 'serial_number', 'part', 'location', 'custom_fields' ]

    def get_custom_fields(self, obj):
        # Get this item's custom fields with most recent Values
        if obj.fieldvalues.exists():
            obj_custom_fields = obj.fieldvalues.filter(is_current=True)
        else:
            obj_custom_fields = None
        # create initial empty dict
        custom_fields = {}

        if obj_custom_fields:
            for field in obj_custom_fields:
                custom_fields[field.field.field_name] = field.field_value
                #custom_fields.update(field.field=field.field_value)

        return custom_fields

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary prefetching of data. """
        queryset = queryset.select_related('location').select_related('part')

        return queryset
