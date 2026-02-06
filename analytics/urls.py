"""
URL routing for analytics app.
"""

from django.urls import path
from analytics.views import (
    DashboardView,
    revenue_analytics,
    top_products,
    low_stock_alert,
    order_status_dist,
    payment_status_dist,
    profit_analysis,
)

urlpatterns = [
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Analytics
    path('revenue/', revenue_analytics, name='revenue'),
    path('top-products/', top_products, name='top-products'),
    path('low-stock/', low_stock_alert, name='low-stock'),
    path('order-status/', order_status_dist, name='order-status'),
    path('payment-status/', payment_status_dist, name='payment-status'),
    path('profit/', profit_analysis, name='profit'),
]
