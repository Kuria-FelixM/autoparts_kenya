"""
Serializers for products and categories.
"""

from rest_framework import serializers
from products.models import Category, Product, ProductImage
from vehicles.serializers import VehicleModelSerializer
from vehicles.models import VehicleModel


class ProductImageSerializer(serializers.ModelSerializer):
    """Product image serializer."""
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'display_order']
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer with product count."""
    products_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon_url', 'image_url',
            'parent', 'is_active', 'display_order', 'products_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Category with nested children."""
    children = CategorySerializer(many=True, read_only=True)
    products_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon_url', 'image_url',
            'parent', 'is_active', 'display_order', 'children', 'products_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_products_count(self, obj):
        """Count active products in this category."""
        return obj.products.filter(is_active=True).count()


class ProductListSerializer(serializers.ModelSerializer):
    """Basic product serializer for list views."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    available_stock = serializers.SerializerMethodField(read_only=True)
    discounted_price = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'category', 'category_name', 'price',
            'discount_percentage', 'discounted_price', 'primary_image',
            'is_featured', 'is_active', 'rating', 'review_count',
            'available_stock', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'available_stock', 'discounted_price'
        ]
    
    def get_available_stock(self, obj):
        return obj.available_stock
    
    def get_discounted_price(self, obj):
        return float(obj.discounted_price)


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed product serializer with compatibility info."""
    category = CategorySerializer(read_only=True)
    compatible_vehicles = VehicleModelSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    
    available_stock = serializers.SerializerMethodField(read_only=True)
    discounted_price = serializers.SerializerMethodField(read_only=True)
    profit_margin = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'description', 'category',
            'compatible_vehicles', 'price', 'cost_price', 'discount_percentage',
            'discounted_price', 'stock', 'reserved_stock', 'available_stock',
            'primary_image', 'images', 'is_featured', 'is_active',
            'rating', 'review_count', 'profit_margin', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'available_stock',
            'discounted_price', 'profit_margin'
        ]
    
    def get_available_stock(self, obj):
        return obj.available_stock
    
    def get_discounted_price(self, obj):
        return float(obj.discounted_price)
    
    def get_profit_margin(self, obj):
        return obj.profit_margin


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating products (owner only).
    Includes stock management and pricing.
    """
    compatible_vehicle_ids = serializers.PrimaryKeyRelatedField(
        queryset=VehicleModel.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='compatible_vehicles'
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'description', 'category',
            'compatible_vehicle_ids', 'price', 'cost_price', 'discount_percentage',
            'stock', 'primary_image', 'is_featured', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        """Create product."""
        compatible_vehicles = validated_data.pop('compatible_vehicles', [])
        product = Product.objects.create(**validated_data)
        product.compatible_vehicles.set(compatible_vehicles)
        return product
    
    def update(self, instance, validated_data):
        """Update product."""
        compatible_vehicles = validated_data.pop('compatible_vehicles', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update vehicle compatibility if provided
        if compatible_vehicles is not None:
            instance.compatible_vehicles.set(compatible_vehicles)
        
        return instance
