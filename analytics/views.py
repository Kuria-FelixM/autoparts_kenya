"""
Analytics views: owner-only business metrics and dashboard data.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.db.models import Sum, Count, Max, Min, Avg, F
from django.utils.timezone import now, timedelta
from datetime import datetime

from core.permissions import IsOwner
from orders.models import Order, OrderItem
from products.models import Product, Category
from payments.models import TransactionLog


class DashboardView(generics.GenericAPIView):
    """
    Owner dashboard with key metrics.
    """
    permission_classes = [IsOwner]
    
    @extend_schema(
        tags=['Admin - Analytics'],
        summary='Get dashboard metrics (Owner only)',
        description='Get key business metrics: revenue, orders, products. Owner-only endpoint.',
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'total_revenue': {'type': 'number'},
                    'total_orders': {'type': 'integer'},
                    'total_products': {'type': 'integer'},
                    'low_stock_products': {'type': 'integer'},
                }
            },
        },
    )
    def get(self, request, *args, **kwargs):
        """Get dashboard summary metrics."""
        low_stock_threshold = 10
        
        # Revenue (paid orders only)
        total_revenue = Order.objects.filter(
            payment_status='paid'
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # Orders
        total_orders = Order.objects.count()
        orders_today = Order.objects.filter(
            created_at__date=now().date()
        ).count()
        
        # Products
        total_products = Product.objects.filter(is_active=True).count()
        
        # Low stock alert
        low_stock = Product.objects.filter(
            stock__lte=low_stock_threshold,
            is_active=True
        ).count()
        
        return Response({
            'total_revenue': float(total_revenue),
            'total_revenue_currency': 'KSh',
            'total_orders': total_orders,
            'orders_today': orders_today,
            'total_products': total_products,
            'low_stock_products': low_stock,
            'low_stock_threshold': low_stock_threshold,
            'generated_at': now().isoformat(),
        })


@api_view(['GET'])
@permission_classes([IsOwner])
@extend_schema(
    tags=['Admin - Analytics'],
    summary='Get revenue analytics',
    description='Revenue metrics: total, by period, growth. Owner-only.',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'total_revenue': {'type': 'number'},
                'revenue_today': {'type': 'number'},
                'revenue_this_week': {'type': 'number'},
                'revenue_this_month': {'type': 'number'},
                'average_order_value': {'type': 'number'},
                'paid_orders': {'type': 'integer'},
            }
        },
    },
)
def revenue_analytics(request):
    """Revenue analytics by period."""
    today = now().date()
    this_week_start = today - timedelta(days=today.weekday())
    this_month_start = today.replace(day=1)
    
    # Total revenue
    total_revenue = Order.objects.filter(
        payment_status='paid'
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Revenue today
    revenue_today = Order.objects.filter(
        payment_status='paid',
        created_at__date=today
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Revenue this week
    revenue_this_week = Order.objects.filter(
        payment_status='paid',
        created_at__date__gte=this_week_start
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Revenue this month
    revenue_this_month = Order.objects.filter(
        payment_status='paid',
        created_at__date__gte=this_month_start
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Average order value
    paid_orders = Order.objects.filter(payment_status='paid')
    aov = paid_orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
    paid_count = paid_orders.count()
    
    return Response({
        'total_revenue': float(total_revenue),
        'revenue_today': float(revenue_today),
        'revenue_this_week': float(revenue_this_week),
        'revenue_this_month': float(revenue_this_month),
        'average_order_value': float(aov),
        'paid_orders_count': paid_count,
        'currency': 'KSh',
    })


@api_view(['GET'])
@permission_classes([IsOwner])
@extend_schema(
    tags=['Admin - Analytics'],
    summary='Get top products',
    description='Best selling products by quantity and revenue. Owner-only.',
    responses={
        200: {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'product_id': {'type': 'integer'},
                    'product_name': {'type': 'string'},
                    'quantity_sold': {'type': 'integer'},
                    'revenue': {'type': 'number'},
                    'rating': {'type': 'number'},
                }
            }
        },
    },
)
def top_products(request):
    """Top selling products."""
    limit = int(request.query_params.get('limit', 10))
    
    top_items = OrderItem.objects.values(
        'product__id', 'product__name', 'product__rating'
    ).annotate(
        quantity_sold=Sum('quantity'),
        revenue=Sum('line_total')
    ).order_by('-revenue')[:limit]
    
    return Response([{
        'product_id': item['product__id'],
        'product_name': item['product__name'],
        'quantity_sold': item['quantity_sold'],
        'revenue': float(item['revenue']),
        'rating': item['product__rating'],
    } for item in top_items])


@api_view(['GET'])
@permission_classes([IsOwner])
@extend_schema(
    tags=['Admin - Analytics'],
    summary='Get low stock alert',
    description='Products below threshold. Owner-only.',
    responses={
        200: {
            'type': 'array',
            'items': {
                'type': 'object',
            }
        },
    },
)
def low_stock_alert(request):
    """Low stock products alert."""
    threshold = int(request.query_params.get('threshold', 10))
    
    low_stock = Product.objects.filter(
        stock__lte=threshold,
        is_active=True
    ).values('id', 'name', 'sku', 'stock', 'reserved_stock', 'category__name').order_by('stock')
    
    return Response([{
        'product_id': item['id'],
        'product_name': item['name'],
        'sku': item['sku'],
        'current_stock': item['stock'],
        'reserved_stock': item['reserved_stock'],
        'available': item['stock'] - item['reserved_stock'],
        'category': item['category__name'],
    } for item in low_stock])


@api_view(['GET'])
@permission_classes([IsOwner])
@extend_schema(
    tags=['Admin - Analytics'],
    summary='Get order status distribution',
    description='Orders grouped by status. Owner-only.',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'pending': {'type': 'integer'},
                'confirmed': {'type': 'integer'},
                'processing': {'type': 'integer'},
                'shipped': {'type': 'integer'},
                'delivered': {'type': 'integer'},
                'cancelled': {'type': 'integer'},
            }
        },
    },
)
def order_status_dist(request):
    """Order distribution by status."""
    distribution = Order.objects.values('order_status').annotate(
        count=Count('id')
    )
    
    result = {
        'pending': 0,
        'confirmed': 0,
        'processing': 0,
        'shipped': 0,
        'delivered': 0,
        'cancelled': 0,
    }
    
    for item in distribution:
        status = item['order_status']
        if status in result:
            result[status] = item['count']
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsOwner])
@extend_schema(
    tags=['Admin - Analytics'],
    summary='Get payment status distribution',
    description='Orders grouped by payment status. Owner-only.',
    responses={
        200: {
            'type': 'object',
        },
    },
)
def payment_status_dist(request):
    """Payment distribution."""
    distribution = Order.objects.values('payment_status').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    )
    
    result = {}
    for item in distribution:
        status = item['payment_status']
        result[status] = {
            'count': item['count'],
            'revenue': float(item['revenue'] or 0),
        }
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsOwner])
@extend_schema(
    tags=['Admin - Analytics'],
    summary='Get profit analysis',
    description='Profit margin analysis for products. Owner-only.',
    responses={
        200: {
            'type': 'object',
        },
    },
)
def profit_analysis(request):
    """Profit margin analysis."""
    products = Product.objects.filter(
        cost_price__isnull=False
    ).annotate(
        total_sold=Sum('order_items__quantity'),
        total_revenue=Sum('order_items__line_total')
    ).values(
        'id', 'name', 'price', 'cost_price', 'total_sold', 'total_revenue'
    )
    
    analysis = []
    total_profit = 0
    
    for product in products:
        if product['total_sold']:
            cost = float(product['cost_price']) * product['total_sold']
            revenue = float(product['total_revenue'] or 0)
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0
            
            total_profit += profit
            
            analysis.append({
                'product_id': product['id'],
                'product_name': product['name'],
                'unit_price': float(product['price']),
                'unit_cost': float(product['cost_price']),
                'quantity_sold': product['total_sold'],
                'total_revenue': revenue,
                'total_cost': cost,
                'profit': profit,
                'margin_percent': round(margin, 2),
            })
    
    analysis_sort = sorted(analysis, key=lambda x: x['profit'], reverse=True)
    
    return Response({
        'products': analysis_sort,
        'total_profit': total_profit,
        'currency': 'KSh',
    })
