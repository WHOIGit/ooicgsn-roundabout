from rest_framework import generics, viewsets, filters
from ..models import Assembly
from .serializers import AssemblySerializer, AssemblyPartSerializer


class AssemblyViewSet(viewsets.ModelViewSet):
    serializer_class = AssemblySerializer
    search_fields = ['name']
    filter_backends = (filters.SearchFilter,)

    def get_queryset(self):
        queryset = Assembly.objects.all()
        # Set up eager loading to avoid N+1 selects
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset
