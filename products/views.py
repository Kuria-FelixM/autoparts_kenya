"""
Product views: categories and products with vehicle compatibility filtering.
Public read access (guest-first), owner-only write access.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.db.models import Q, F, Count, DecimalField
from django.db.models.functions import Coalesce

from core.permissions import IsOwnerOrReadOnly
from core.utils import calculate_delivery_time
from products.models import Category, Product, ProductImage
from products.serializers import (
    CategorySerializer,
    CategoryDetailSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
)
from vehicles.models import VehicleModel


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Product categories.
    Guest-first: GET is public, POST/PUT/DELETE for owner only.
    """
    queryset = Category.objects.prefetch_related('children')
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order', 'name']
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve."""
        if self.action == 'retrieve':
            return CategoryDetailSerializer
        return CategorySerializer
    
    def get_queryset(self):
        """Filter out inactive categories unless user is owner."""
        qs = super().get_queryset()
        if not (self.request.user and self.request.user.is_authenticated and hasattr(self.request.user, 'profile') and self.request.user.profile.is_owner):
            qs = qs.filter(is_active=True)
        return qs
    
    @extend_schema(
        tags=['Products - Categories'],
        summary='List product categories',
        description='Get all product categories. Public endpoint (no authentication required).',
        parameters=[
            OpenApiParameter(
                name='search',
                description='Search by name or description',
                required=False,
                type=str,
            ),
        ],
        responses={
            200: CategorySerializer(many=True),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Products - Categories'],
        summary='Get category details',
        description='Retrieve a category with subcategories.',
        responses={
            200: CategoryDetailSerializer,
            404: {'description': 'Category not found'},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Products - Categories'],
        summary='Create category (Owner only)',
        request=CategorySerializer,
        responses={
            201: CategorySerializer,
            401: {'description': 'Unauthorized'},
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Products - Categories'],
        summary='Update category (Owner only)',
        request=CategorySerializer,
        responses={
            200: CategorySerializer,
            401: {'description': 'Unauthorized'},
            404: {'description': 'Category not found'},
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Products - Categories'],
        summary='Delete category (Owner only)',
        responses={
            204: {'description': 'Category deleted'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Category not found'},
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ProductViewSet(viewsets.ModelViewSet):
    """
    Products with vehicle compatibility filtering.
    Advanced filters: vehicle make, model, year, category, price range, etc.
    Guest-first: GET is public, POST/PUT/DELETE for owner only.
    """
    queryset = Product.objects.prefetch_related('compatible_vehicles', 'images', 'category').filter(is_active=True)
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured']
    search_fields = ['name', 'slug', 'sku', 'description']
    ordering_fields = ['price', 'rating', 'review_count', 'created_at', 'stock']
    ordering = ['-is_featured', '-created_at']
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve, create for write."""
        if self.action == 'retrieve':
            return ProductDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductListSerializer
    
    def get_queryset(self):
        """Add vehicle compatibility filtering."""
        qs = super().get_queryset()
        
        # Filter by vehicle compatibility
        vehicle_make = self.request.query_params.get('vehicle_make')
        vehicle_model = self.request.query_params.get('vehicle_model')
        vehicle_year = self.request.query_params.get('vehicle_year')
        
        if vehicle_year:
            try:
                year = int(vehicle_year)
                # Find compatible vehicles for this year
                compatible_models = VehicleModel.objects.filter(
                    year_from__lte=year,
                    year_to__gte=year
                )
                if vehicle_make:
                    compatible_models = compatible_models.filter(make__id=vehicle_make)
                if vehicle_model:
                    compatible_models = compatible_models.filter(id=vehicle_model)
                
                qs = qs.filter(compatible_vehicles__in=compatible_models).distinct()
            except (ValueError, TypeError):
                pass
        
        # Price filtering
        price_min = self.request.query_params.get('price_min')
        price_max = self.request.query_params.get('price_max')
        
        if price_min:
            try:
                qs = qs.filter(price__gte=float(price_min))
            except (ValueError, TypeError):
                pass
        
        if price_max:
            try:
                qs = qs.filter(price__lte=float(price_max))
            except (ValueError, TypeError):
                pass
        
        # In stock only
        in_stock_only = self.request.query_params.get('in_stock', 'false').lower() == 'true'
        if in_stock_only:
            qs = qs.exclude(stock=0)
        
        return qs
    
    @extend_schema(
        tags=['Products - Products'],
        summary='List products with vehicle filtering',
        description='Get all products with advanced filtering by vehicle, price, category, etc. Public endpoint.',
        parameters=[
            OpenApiParameter(
                name='vehicle_make',
                description='Filter by vehicle make ID',
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name='vehicle_model',
                description='Filter by vehicle model ID',
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name='vehicle_year',
                description='Filter by vehicle year (finds compatible models)',
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name='category',
                description='Filter by category ID',
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name='price_min',
                description='Minimum price (KSh)',
                required=False,
                type=float,
            ),
            OpenApiParameter(
                name='price_max',
                description='Maximum price (KSh)',
                required=False,
                type=float,
            ),
            OpenApiParameter(
                name='in_stock',
                description='Filter to in-stock items only (true/false)',
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name='search',
                description='Search by name, SKU, or description',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='ordering',
                description='Order by: price, rating, created_at, stock',
                required=False,
                type=str,
            ),
        ],
        responses={
            200: ProductListSerializer(many=True),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Products - Products'],
        summary='Get product details',
        description='Retrieve full product details with vehicle compatibility and images.',
        responses={
            200: ProductDetailSerializer,
            404: {'description': 'Product not found'},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Products - Products'],
        summary='Create product (Owner only)',
        description='Add a new product with vehicle compatibility. Owner-only endpoint.',
        request=ProductCreateUpdateSerializer,
        responses={
            201: ProductCreateUpdateSerializer,
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
        },
        examples=[
            OpenApiExample(
                'example_product',
                summary='Example product',
                value={
                    'name': 'Engine Oil Filter',
                    'slug': 'engine-oil-filter',
                    'sku': 'FILTER-001',
                    'description': 'High-quality engine oil filter',
                    'category': 1,
                    'compatible_vehicle_ids': [1, 2, 3],
                    'price': 950.00,
                    'cost_price': 500.00,
                    'discount_percentage': 5,
                    'stock': 50,
                    'is_featured': True,
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Products - Products'],
        summary='Update product (Owner only)',
        request=ProductCreateUpdateSerializer,
        responses={
            200: ProductCreateUpdateSerializer,
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Product not found'},
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Products - Products'],
        summary='Delete product (Owner only)',
        responses={
            204: {'description': 'Product deleted'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Product not found'},
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Products - Products'],
        summary='Get featured products',
        description='Get featured/promoted products for homepage.',
        responses={
            200: ProductListSerializer(many=True),
        },
    )
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products."""
        featured_products = self.get_queryset().filter(is_featured=True)[:12]
        serializer = ProductListSerializer(featured_products, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Products - Products'],
        summary='Get products by vehicle compatibility',
        description='Find all products compatible with a specific vehicle year/make/model.',
        parameters=[
            OpenApiParameter('vehicle_year', type=int, required=True, location='query'),
            OpenApiParameter('vehicle_make', type=int, required=False, location='query'),
            OpenApiParameter('vehicle_model', type=int, required=False, location='query'),
        ],
        responses={
            200: ProductListSerializer(many=True),
        },
    )
    @action(detail=False, methods=['get'])
    def by_vehicle(self, request):
        """Get products for specific vehicle year."""
        vehicle_year = request.query_params.get('vehicle_year')
        if not vehicle_year:
            return Response(
                {'error': 'vehicle_year parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(vehicle_year)
        except ValueError:
            return Response(
                {'error': 'vehicle_year must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build query using existing filter logic
        self.request = request  # Ensure request context
        products = self.get_queryset()
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
