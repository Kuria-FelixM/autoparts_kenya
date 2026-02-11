"""
URL routing for products app.
"""

from django.urls import path, include
from django.urls import converters
from rest_framework.routers import DefaultRouter

from products.views import CategoryViewSet, ProductViewSet

# Workaround for DRF converter registration issue
if 'drf_format_suffix' in converters.REGISTERED_CONVERTERS:
    del converters.REGISTERED_CONVERTERS['drf_format_suffix']

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]