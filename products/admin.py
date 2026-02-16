"""
Django admin configuration for products.
Enables manual creation and management of categories and products.
"""

from django.contrib import admin
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    """
    Inline admin for product images.
    Allows adding/editing images directly from the product admin.
    """
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'display_order']
    ordering = ['display_order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for product categories.
    Supports hierarchical categories (parent/child relationships).
    """
    list_display = ['name', 'parent', 'is_active', 'display_order', 'created_at']
    search_fields = ['name', 'slug']
    list_filter = ['is_active', 'parent', 'created_at']
    list_editable = ['display_order', 'is_active']
    ordering = ['display_order', 'name']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'parent')
        }),
        ('Description & Display', {
            'fields': ('description', 'display_order')
        }),
        ('Media', {
            'fields': ('icon_url', 'image_url'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for products with vehicle compatibility.
    Includes inline image management and pricing controls.
    """
    list_display = ['name', 'sku', 'category', 'price', 'stock', 'is_active', 'is_featured']
    search_fields = ['name', 'sku', 'category__name']
    list_filter = ['category', 'is_active', 'is_featured', 'created_at']
    list_editable = ['is_active', 'is_featured']
    ordering = ['-created_at']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('SKU & Pricing', {
            'fields': ('sku', 'price', 'cost_price', 'discount_percentage')
        }),
        ('Inventory', {
            'fields': ('stock', 'reserved_stock'),
            'description': 'Available stock = stock - reserved_stock'
        }),
        ('Vehicle Compatibility', {
            'fields': ('compatible_vehicles',),
            'description': 'Select which vehicle models are compatible with this product'
        }),
        ('Images', {
            'fields': ('primary_image',)
        }),
        ('Rating & Status', {
            'fields': ('rating', 'review_count', 'is_featured', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'rating', 'review_count']
    filter_horizontal = ['compatible_vehicles']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """
    Admin interface for individual product images.
    """
    list_display = ['product', 'alt_text', 'display_order', 'created_at']
    search_fields = ['product__name', 'alt_text']
    list_filter = ['product__category', 'created_at']
    list_editable = ['display_order']
    ordering = ['product', 'display_order']
    
    fieldsets = (
        ('Image Information', {
            'fields': ('product', 'image', 'alt_text')
        }),
        ('Display', {
            'fields': ('display_order',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
