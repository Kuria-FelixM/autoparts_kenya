"""
URL routing for users app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import (
    RegistrationView,
    ProfileView,
    SavedVehicleViewSet,
    SavedAddressViewSet,
)

router = DefaultRouter()
router.register(r'saved-vehicles', SavedVehicleViewSet, basename='saved-vehicle')
router.register(r'saved-addresses', SavedAddressViewSet, basename='saved-address')

urlpatterns = [
    # JWT Authentication
    path('register/', RegistrationView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile & Settings
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Nested routes
    path('', include(router.urls)),
]
