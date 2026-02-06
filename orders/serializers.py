"""
Serializers for orders and checkout.
Supports both guest and authenticated users.
"""

from rest_framework import serializers
from orders.models import Order, OrderItem
from products.models import Product
from core.utils import calculate_order_total_with_delivery
from decimal import Decimal


class OrderItemSerializer(serializers.ModelSerializer):
    """Line item in order."""
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'unit_price',
            'quantity', 'line_total', 'created_at'
        ]
        read_only_fields = ['id', 'product_name', 'product_sku', 'line_total', 'created_at']


class OrderItemCreateSerializer(serializers.Serializer):
    """
    Item for order creation (checkout).
    Validates product availability and pricing.
    """
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=100)
    
    def validate_product_id(self, value):
        """Check product exists and is active."""
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError('Bidhaa haipo au haijaidhiniwi. (Product not found or inactive.)')
        return value
    
    def validate(self, data):
        """Check stock availability."""
        product = Product.objects.get(id=data['product_id'])
        if product.available_stock < data['quantity']:
            raise serializers.ValidationError({
                'quantity': f'Stock haifiki. Inataka: {data["quantity"]}, Iliyopo: {product.available_stock}'
            })
        return data


class OrderListSerializer(serializers.ModelSerializer):
    """Order list view (summary)."""
    item_count = serializers.SerializerMethodField(read_only=True)
    customer_email = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'customer_email', 'delivery_city',
            'subtotal', 'delivery_cost', 'total_amount', 'order_status',
            'payment_status', 'item_count', 'created_at'
        ]
        read_only_fields = fields
    
    def get_item_count(self, obj):
        return obj.get_item_count()
    
    def get_customer_email(self, obj):
        return obj.customer_email


class OrderDetailSerializer(serializers.ModelSerializer):
    """Order detail view with items."""
    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.SerializerMethodField(read_only=True)
    customer_phone = serializers.SerializerMethodField(read_only=True)
    item_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'customer_email', 'customer_phone',
            'guest_email', 'guest_phone', 'delivery_address', 'delivery_city',
            'delivery_postal_code', 'recipient_name', 'recipient_phone',
            'subtotal', 'delivery_cost', 'total_amount', 'order_status',
            'payment_status', 'customer_notes', 'admin_notes', 'items',
            'item_count', 'created_at', 'updated_at', 'paid_at',
            'shipped_at', 'delivered_at'
        ]
        read_only_fields = fields
    
    def get_customer_email(self, obj):
        return obj.customer_email
    
    def get_customer_phone(self, obj):
        return obj.customer_phone
    
    def get_item_count(self, obj):
        return obj.get_item_count()


class OrderCreateSerializer(serializers.Serializer):
    """
    Order creation (checkout) endpoint.
    Supports both guest and authenticated users.
    """
    # Cart items
    items = OrderItemCreateSerializer(many=True, required=True)
    
    # Delivery
    delivery_address = serializers.CharField(max_length=1000, required=True)
    delivery_city = serializers.CharField(max_length=100, default='Nairobi')
    delivery_postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Recipient
    recipient_name = serializers.CharField(max_length=255, required=True)
    recipient_phone = serializers.CharField(max_length=15, required=True)
    
    # Guest fields (if not authenticated)
    guest_email = serializers.EmailField(required=False)
    
    # Optional
    customer_notes = serializers.CharField(required=False, allow_blank=True)
    delivery_type = serializers.ChoiceField(
        choices=['standard', 'express', 'economy'],
        default='standard'
    )
    
    def validate(self, data):
        """
        Validate checkout data.
        - At least one item
        - Guest must provide email
        - Check stock for all items
        """
        items = data.get('items', [])
        if not items:
            raise serializers.ValidationError({'items': 'Hakuna bidhaa kwenye karata. (Cart is empty.)'})
        
        # Get authenticated user from context
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        
        # Guest checkout requires email
        if not user and not data.get('guest_email'):
            raise serializers.ValidationError({
                'guest_email': 'Tafadhali ingiza barua kwa uteuzi wa mgeni. (Email required for guest checkout.)'
            })
        
        return data
    
    def create(self, validated_data):
        """
        Create order from validated data.
        Validates final pricing and stock, then creates Order + OrderItems.
        """
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        
        items_data = validated_data.pop('items')
        delivery_address = validated_data.pop('delivery_address')
        delivery_city = validated_data.pop('delivery_city', 'Nairobi')
        delivery_postal_code = validated_data.pop('delivery_postal_code', '')
        recipient_name = validated_data.pop('recipient_name')
        recipient_phone = validated_data.pop('recipient_phone')
        customer_notes = validated_data.pop('customer_notes', '')
        guest_email = validated_data.pop('guest_email', '')
        delivery_type = validated_data.pop('delivery_type', 'standard')
        
        # Calculate order totals
        subtotal = Decimal('0.00')
        order_items_data = []
        
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            quantity = item_data['quantity']
            unit_price = product.discounted_price
            line_total = unit_price * quantity
            subtotal += line_total
            
            order_items_data.append({
                'product': product,
                'product_name': product.name,
                'product_sku': product.sku,
                'unit_price': unit_price,
                'quantity': quantity,
            })
        
        # Calculate delivery cost
        delivery_info = calculate_order_total_with_delivery(
            subtotal, delivery_city, delivery_type
        )
        delivery_cost = delivery_info['delivery_cost']
        total_amount = delivery_info['total']
        
        # Create order
        order = Order.objects.create(
            user=user,
            guest_email=guest_email,
            guest_phone=recipient_phone,
            delivery_address=delivery_address,
            delivery_city=delivery_city,
            delivery_postal_code=delivery_postal_code,
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
            subtotal=subtotal,
            delivery_cost=delivery_cost,
            total_amount=total_amount,
            customer_notes=customer_notes,
        )
        
        # Create order items
        for item_data in order_items_data:
            product = item_data.pop('product')
            OrderItem.objects.create(order=order, **item_data)
            
            # Reserve stock
            product.reserved_stock += item_data['quantity']
            product.save(update_fields=['reserved_stock'])
        
        return order
