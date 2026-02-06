"""
Order models: checkout flow for guest & authenticated users.
"""

from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from decimal import Decimal


class Order(models.Model):
    """
    Customer order (guest checkout or authenticated).
    Guest orders: user=None, guest_email/guest_phone captured.
    Authenticated orders: linked to User.
    """
    ORDER_STATUSES = [
        ('pending', 'Kutaka (Pending)'),
        ('confirmed', 'Imekubaliana (Confirmed)'),
        ('processing', 'Inafanya (Processing)'),
        ('shipped', 'Imetumwa (Shipped)'),
        ('delivered', 'Imewasili (Delivered)'),
        ('cancelled', 'Imeghairi (Cancelled)'),
    ]
    
    PAYMENT_STATUSES = [
        ('unpaid', 'Haijalipiwa (Unpaid)'),
        ('pending', 'Inangoja (Pending payment)'),
        ('paid', 'Nelipwa (Paid)'),
        ('failed', 'Imeshindwa (Failed)'),
        ('refunded', 'Imerjeishwa (Refunded)'),
    ]
    
    # User info (authenticated or guest)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Guest checkout info
    guest_email = models.EmailField(blank=True, help_text='For guest orders')
    guest_phone = models.CharField(max_length=15, blank=True, help_text='For guest orders')
    
    # Order tracking number
    order_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        editable=False
    )
    
    # Delivery info
    delivery_address = models.TextField()
    delivery_city = models.CharField(max_length=100, default='Nairobi')
    delivery_postal_code = models.CharField(max_length=20, blank=True)
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=15)
    
    # Pricing (in KSh)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status tracking
    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUSES,
        default='pending'
    )
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUSES,
        default='unpaid'
    )
    
    # Notes
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True, help_text='Timestamp when payment confirmed')
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders_order'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user']),
            models.Index(fields=['order_status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'Order {self.order_number}'
    
    def save(self, *args, **kwargs):
        """Generate order number if not exists."""
        if not self.order_number:
            from django.utils.timezone import now
            timestamp = now().strftime('%Y%m%d%H%M%S')
            self.order_number = f'ORD-{timestamp}'
        super().save(*args, **kwargs)
    
    @property
    def customer_email(self):
        """Get customer email (from user or guest)."""
        if self.user:
            return self.user.email
        return self.guest_email
    
    @property
    def customer_phone(self):
        """Get customer phone (from guest or user profile)."""
        if self.guest_phone:
            return self.guest_phone
        if self.user and hasattr(self.user, 'profile'):
            return self.user.profile.phone_number
        return ''
    
    def get_item_count(self):
        """Total items in order."""
        return self.items.aggregate(models.Sum('quantity'))['quantity__sum'] or 0


class OrderItem(models.Model):
    """
    Line item in order.
    Stores product snapshot (price, name) at time of order.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )
    
    # Snapshot of product at time of order
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    
    # Subtotal for this line
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'orders_item'
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.product_name} x{self.quantity}'
    
    def save(self, *args, **kwargs):
        """Auto-calculate line total."""
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)
