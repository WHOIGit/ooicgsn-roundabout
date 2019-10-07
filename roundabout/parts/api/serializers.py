from rest_framework import serializers
from ..models import Part, PartType


class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = ('id', 'name', 'friendly_name', 'part_number', 'unit_cost', 'refurbishment_cost' )
