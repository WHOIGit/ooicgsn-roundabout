from rest_framework import generics, viewsets, filters
from ..models import Part
from .serializers import PartSerializer


class PartViewSet(viewsets.ModelViewSet):

    queryset = Part.objects.all()
    serializer_class = PartSerializer
    search_fields = ['part_number']
    filter_backends = (filters.SearchFilter,)
