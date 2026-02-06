"""
Product models: categories and products with vehicle compatibility.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from vehicles.models import VehicleModel


class Category(models.Model):
    """
    Product category (e.g., Engine Parts, Brake Systems, Electrical).
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    # Display
    icon_url = models.URLField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    
    # Hierarchy (optional subcategories)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        help_text='Parent category for subcategories'
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text='Order for display')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products_category'
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Product with vehicle compatibility via ManyToMany to VehicleModel.
    Supports images and inventory tracking.
    """
    # Basic info
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    
    # Vehicle compatibility
    compatible_vehicles = models.ManyToManyField(
        VehicleModel,
        related_name='products',
        help_text='Vehicle models compatible with this product'
    )
    
    # Business info
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Pricing (in KSh)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Optional: cost price for owner analytics
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text='Owner-only: cost price for margin calculation'
    )
    
    # Optional: discount
    discount_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Discount as percentage (0-100)'
    )
    
    # Inventory
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    reserved_stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Stock reserved for pending orders'
    )
    
    # Images
    primary_image = models.ImageField(
        upload_to='products/%Y/%m/',
        null=True,
        blank=True
    )
    
    # Metadata
    is_featured = models.BooleanField(default=False, help_text='Show on homepage')
    is_active = models.BooleanField(default=True)
    
    # Ratings (optional - for future feature)
    rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='Average rating (0-5)'
    )
    review_count = models.IntegerField(default=0, help_text='Total reviews')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products_product'
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['is_active']),
            models.Index(fields=['category']),
            models.Index(fields=['stock']),
        ]
    
    def __str__(self):
        return f'{self.name} ({self.sku})'
    
    @property
    def available_stock(self):
        """Available stock = total - reserved."""
        return max(0, self.stock - self.reserved_stock)
    
    @property
    def discounted_price(self):
        """Price after discount."""
        if self.discount_percentage:
            discount = self.price * self.discount_percentage / 100
            return self.price - discount
        return self.price
    
    @property
    def profit_margin(self):
        """Profit margin percentage (only if cost_price is set)."""
        if self.cost_price and self.cost_price > 0:
            margin = ((self.price - self.cost_price) / self.price) * 100
            return round(margin, 2)
        return None
    
    def is_in_stock(self):
        """Check if product is in stock."""
        return self.available_stock > 0


class ProductImage(models.Model):
    """
    Additional product images (gallery).
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/%Y/%m/')
    alt_text = models.CharField(max_length=100, blank=True)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'products_image'
        ordering = ['display_order', 'created_at']
    
    def __str__(self):
        return f'Image for {self.product.name}'
