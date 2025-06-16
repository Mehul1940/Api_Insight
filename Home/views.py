from rest_framework import viewsets
from .models import Department, CityMonitoring
from rest_framework.parsers import MultiPartParser, FormParser
from Home.serializer import DepartmentSerializer, CityMonitoringSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class CityMonitoringViewSet(viewsets.ModelViewSet):
    queryset = CityMonitoring.objects.all()
    serializer_class = CityMonitoringSerializer
    parser_classes = (MultiPartParser, FormParser)  # Support file uploads

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()
