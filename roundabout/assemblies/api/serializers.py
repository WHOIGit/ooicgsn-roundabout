from rest_framework import serializers

from ..models import Assembly, AssemblyPart, AssemblyType
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


class AssemblyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssemblyType
        fields = ['name']


class AssemblySerializer(serializers.ModelSerializer):
    assembly_parts = AssemblyPartSerializer(many=True, read_only=True)
    assembly_type = AssemblyTypeSerializer(read_only=True)

    class Meta:
        model = Assembly
        fields = ['id', 'name', 'assembly_number', 'description', 'assembly_type', 'assembly_parts' ]

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary prefetching of data. """
        queryset = queryset.prefetch_related('assembly_parts')

        return queryset
