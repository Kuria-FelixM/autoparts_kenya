"""
URL routing for payments app.
"""

from django.urls import path
from payments.views import (
    STKPushInitiateView,
    mpesa_callback_webhook,
    check_payment_status,
)

urlpatterns = [
    # M-Pesa payment
    path('initiate-stk-push/', STKPushInitiateView.as_view(), name='stk-push-initiate'),
    path('mpesa-callback/', mpesa_callback_webhook, name='mpesa-callback'),
    path('check-status/', check_payment_status, name='check-status'),
]
