from rest_framework import serializers

from ..models import Assembly, AssemblyPart
from roundabout.parts.api.serializers import PartSerializer


class AssemblyPartSerializer(serializers.ModelSerializer):
    part = PartSerializer(read_only=True)

    class Meta:
        model = AssemblyPart
        fields = ['id', 'part', 'parent', 'note', 'order' ]

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary prefetching of data. """
        queryset = queryset.select_related('part')

        return queryset


class AssemblySerializer(serializers.ModelSerializer):
    assembly_parts = AssemblyPartSerializer(many=True, read_only=True)

    class Meta:
        model = Assembly
        fields = ['id', 'name', 'assembly_parts', 'assembly_number', 'description' ]

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary prefetching of data. """
        queryset = queryset.prefetch_related('assembly_parts')

        return queryset
