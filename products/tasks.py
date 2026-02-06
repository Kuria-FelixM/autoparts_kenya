"""
Celery tasks for products app.
"""

from celery import shared_task
from django.conf import settings
from products.models import Product


@shared_task
def check_low_stock():
    """
    Check for low stock items and notify owner.
    Scheduled to run hourly via Celery Beat.
    """
    low_stock_threshold = settings.LOW_STOCK_THRESHOLD
    low_stock_products = Product.objects.filter(
        stock__lte=low_stock_threshold,
        is_active=True
    )
    
    if low_stock_products.exists():
        # TODO: Send notification to owner (email, SMS via Celery tasks)
        print(f'⚠️ Low stock alert: {low_stock_products.count()} products')
        
        # Log for dashboard analytics
        for product in low_stock_products:
            print(f'  - {product.name}: {product.stock} units')
    
    return low_stock_products.count()
