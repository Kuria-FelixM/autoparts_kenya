"""
URL routing for orders app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from orders.views import (
    CheckoutView,
    OrderListView,
    OrderDetailView,
    OwnerOrdersViewSet,
)

router = DefaultRouter()
router.register(r'admin/orders', OwnerOrdersViewSet, basename='admin-orders')

urlpatterns = [
    # Checkout
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    
    # Order history
    path('my-orders/', OrderListView.as_view(), name='my-orders'),
    path('order/<str:order_number>/', OrderDetailView.as_view(), name='order-detail'),
    
    # Admin routes
    path('', include(router.urls)),
]
