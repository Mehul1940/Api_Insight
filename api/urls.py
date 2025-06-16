from django.urls import path, include
from rest_framework.routers import DefaultRouter
from Home.views import DepartmentViewSet, CityMonitoringViewSet

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'city-monitoring', CityMonitoringViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
