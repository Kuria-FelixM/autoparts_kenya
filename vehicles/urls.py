"""
URL routing for vehicles app.
"""

from django.urls import path, include
from django.urls import converters
from rest_framework.routers import DefaultRouter

from vehicles.views import VehicleMakeViewSet, VehicleModelViewSet

# Workaround for DRF converter registration issue
if 'drf_format_suffix' in converters.REGISTERED_CONVERTERS:
    del converters.REGISTERED_CONVERTERS['drf_format_suffix']

router = DefaultRouter()
router.register(r'makes', VehicleMakeViewSet, basename='vehicle-make')
router.register(r'models', VehicleModelViewSet, basename='vehicle-model')

urlpatterns = [
    path('', include(router.urls)),
]