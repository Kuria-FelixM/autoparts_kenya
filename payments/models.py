"""
Payment models: M-Pesa transaction logging.
"""

from django.db import models
from orders.models import Order


class TransactionLog(models.Model):
    """
    M-Pesa transaction log for audit and debugging.
    Captures all STK Push requests, callbacks, and confirmations.
    """
    TRANSACTION_TYPES = [
        ('stk_initiate', 'STK Push Initiated'),
        ('stk_timeout', 'STK Push Timed Out'),
        ('user_cancel', 'User Cancelled'),
        ('payment_success', 'Payment Successful'),
        ('payment_failed', 'Payment Failed'),
        ('payment_pending', 'Payment Pending'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )
    
    # M-Pesa response data
    merchant_request_id = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, db_index=True)
    
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Response codes
    response_code = models.CharField(max_length=10, blank=True)
    response_description = models.CharField(max_length=255, blank=True)
    
    # Receipt (for successful payments)
    mpesa_receipt = models.CharField(max_length=50, blank=True)
    
    # Raw response data (for debugging)
    raw_response = models.JSONField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_transaction_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'{self.get_transaction_type_display()} - Order {self.order.order_number}'
