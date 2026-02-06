"""
URL routing for vehicles app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from vehicles.views import VehicleMakeViewSet, VehicleModelViewSet

router = DefaultRouter()
router.register(r'makes', VehicleMakeViewSet, basename='vehicle-make')
router.register(r'models', VehicleModelViewSet, basename='vehicle-model')

urlpatterns = [
    path('', include(router.urls)),
]
