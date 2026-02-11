"""
Order views: checkout, order history, order management.
Guest checkout allowed, order history for authenticated only.
"""

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.db.models import Q

from core.permissions import IsOwner
from orders.models import Order, OrderItem
from orders.serializers import (
    OrderCreateSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
)


class CheckoutView(generics.CreateAPIView):
    """
    Checkout endpoint - supports both guest and authenticated users.
    Guest checkout: provide guest_email
    Authenticated: automatic user assignment, can save to order history
    
    Returns order number + payment initiation details.
    """
    serializer_class = OrderCreateSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Orders - Checkout'],
        summary='Create order (guest or authenticated)',
        description='Checkout endpoint. Guests provide email, authenticated users auto-linked. Returns order with payment details.',
        request=OrderCreateSerializer,
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'order': {'type': 'object'},
                    'payment_url': {'type': 'string', 'description': 'M-Pesa STK Push initiation URL'},
                }
            },
            400: {'description': 'Invalid cart or delivery info'},
        },
        examples=[
            OpenApiExample(
                'example_checkout',
                summary='Example checkout',
                value={
                    'items': [
                        {
                            'product_id': 1,
                            'quantity': 2,
                        },
                        {
                            'product_id': 3,
                            'quantity': 1,
                        },
                    ],
                    'delivery_address': '123 Kenyatta Avenue, Nairobi',
                    'delivery_city': 'Nairobi',
                    'delivery_postal_code': '00100',
                    'recipient_name': 'John Doe',
                    'recipient_phone': '+254712345678',
                    'guest_email': 'john@example.com',
                    'customer_notes': 'Please leave with security if not home',
                    'delivery_type': 'standard',
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        return Response(
            {
                'order': OrderDetailSerializer(order).data,
                'message': 'Agizo limejifungua! Kuendelea na malipo. (Order created! Proceed to payment.)',
                'next_step': f'/api/v1/payments/initiate-stk-push/?order_id={order.id}',
            },
            status=status.HTTP_201_CREATED
        )


class OrderListView(generics.ListAPIView):
    """
    Authenticated user's order history.
    Users can only see their own orders.
    """
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only return orders for authenticated user."""
        return Order.objects.filter(user=self.request.user)
    
    @extend_schema(
        tags=['Orders - History'],
        summary='Get user order history',
        description='Retrieve authenticated user\'s order history.',
        parameters=[
            OpenApiParameter(
                name='order_status',
                description='Filter by order status',
                required=False,
                type=str,
                enum=['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'],
            ),
            OpenApiParameter(
                name='payment_status',
                description='Filter by payment status',
                required=False,
                type=str,
                enum=['unpaid', 'pending', 'paid', 'failed', 'refunded'],
            ),
        ],
        responses={
            200: OrderListSerializer(many=True),
            401: {'description': 'Unauthorized'},
        },
    )
    def get(self, request, *args, **kwargs):
        # Optional filtering
        order_status = request.query_params.get('order_status')
        payment_status = request.query_params.get('payment_status')
        
        qs = self.get_queryset()
        
        if order_status:
            qs = qs.filter(order_status=order_status)
        if payment_status:
            qs = qs.filter(payment_status=payment_status)
        
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class OrderDetailView(generics.RetrieveAPIView):
    """
    Order details endpoint.
    Customers can view their own orders (authenticated or guest with order_number).
    Owner can view any order.
    """
    serializer_class = OrderDetailSerializer
    lookup_field = 'order_number'
    
    def get_permissions(self):
        """Allow anyone to view order by number, but restrict by permission logic."""
        return [AllowAny()]
    
    def get_object(self):
        """Retrieve order and check permissions."""
        order_number = self.kwargs.get('order_number')
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return None
        
        # Check access permissions
        request = self.request
        is_owner = (request.user and request.user.is_authenticated and 
                   hasattr(request.user, 'profile') and request.user.profile.is_owner)
        is_customer = order.user == request.user
        
        if not (is_owner or is_customer):
            self.permission_denied(request)
        
        return order
    
    @extend_schema(
        tags=['Orders - History'],
        summary='Get order details',
        description='Retrieve order details by order number. Customers see their own orders, owner can see all.',
        parameters=[
            OpenApiParameter(
                name='order_number',
                description='Order number (e.g., ORD-20250206144530)',
                required=True,
                type=str,
                location='path',
            ),
        ],
        responses={
            200: OrderDetailSerializer,
            401: {'description': 'Unauthorized (not order customer)'},
            404: {'description': 'Order not found'},
        },
    )
    def get(self, request, *args, **kwargs):
        order = self.get_object()
        if not order:
            return Response(
                {'error': 'Agizo halijulikani. (Order not found.)'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(order)
        return Response(serializer.data)


class OwnerOrdersViewSet(viewsets.ViewSet):
    """
    Owner-only endpoint for order management.
    List all orders, update status, mark as shipped/delivered.
    """
    permission_classes = [IsOwner]
    
    @extend_schema(
        tags=['Admin - Orders'],
        summary='List all orders (Owner only)',
        description='Get all customer orders for management. Owner-only endpoint.',
        parameters=[
            OpenApiParameter(
                name='order_status',
                description='Filter by order status',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='payment_status',
                description='Filter by payment status',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='search',
                description='Search by order number or customer email',
                required=False,
                type=str,
            ),
        ],
        responses={
            200: OrderListSerializer(many=True),
            401: {'description': 'Unauthorized - owner access required'},
        },
    )
    def list(self, request):
        """List all orders with optional filtering."""
        qs = Order.objects.all()
        
        order_status = request.query_params.get('order_status')
        payment_status = request.query_params.get('payment_status')
        search = request.query_params.get('search')
        
        if order_status:
            qs = qs.filter(order_status=order_status)
        if payment_status:
            qs = qs.filter(payment_status=payment_status)
        if search:
            qs = qs.filter(
                Q(order_number__icontains=search) |
                Q(guest_email__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        serializer = OrderListSerializer(qs, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Admin - Orders'],
        summary='Get order details (Owner only)',
        description='Retrieve full order details including items.',
        responses={
            200: OrderDetailSerializer,
            404: {'description': 'Order not found'},
        },
    )
    def retrieve(self, request, pk=None):
        """Get order by ID."""
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Agizo halijulikani.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Admin - Orders'],
        summary='Update order (Owner only)',
        description='Update order status and notes.',
        request={
            'type': 'object',
            'properties': {
                'order_status': {'type': 'string', 'enum': ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']},
                'payment_status': {'type': 'string', 'enum': ['unpaid', 'pending', 'paid', 'failed', 'refunded']},
                'admin_notes': {'type': 'string'},
            }
        },
        responses={
            200: OrderDetailSerializer,
            404: {'description': 'Order not found'},
        },
    )
    def partial_update(self, request, pk=None):
        """Update order status and notes."""
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Agizo halijulikani.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        order_status = request.data.get('order_status')
        payment_status = request.data.get('payment_status')
        admin_notes = request.data.get('admin_notes')
        
        if order_status:
            order.order_status = order_status
        if payment_status:
            order.payment_status = payment_status
        if admin_notes:
            order.admin_notes = admin_notes
        
        order.save()
        
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)
