"""
Vehicle views: makes and models.
Public read access (guest-first), owner-only write access.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from core.permissions import IsOwnerOrReadOnly
from vehicles.models import VehicleMake, VehicleModel
from vehicles.serializers import (
    VehicleMakeSerializer,
    VehicleMakeDetailSerializer,
    VehicleModelSerializer,
    VehicleModelDetailSerializer,
)


class VehicleMakeViewSet(viewsets.ModelViewSet):
    """
    Vehicle makes (manufacturers).
    Guest-first: GET is public, POST/PUT/DELETE for owner only.
    """
    queryset = VehicleMake.objects.all()
    serializer_class = VehicleMakeSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'country']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve."""
        if self.action == 'retrieve':
            return VehicleMakeDetailSerializer
        return VehicleMakeSerializer
    
    @extend_schema(
        tags=['Vehicles - Makes'],
        summary='List vehicle makes',
        description='Get all vehicle manufacturers. Public endpoint (no authentication required).',
        parameters=[
            OpenApiParameter(
                name='search',
                description='Search by name or country',
                required=False,
                type=str,
                location='query',
                examples=[OpenApiExample('example', value='Toyota')]
            ),
            OpenApiParameter(
                name='ordering',
                description='Order by name or created_at',
                required=False,
                type=str,
                location='query',
            ),
        ],
        responses={
            200: VehicleMakeSerializer(many=True),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Vehicles - Makes'],
        summary='Get make details with models',
        description='Retrieve a vehicle make with its models.',
        responses={
            200: VehicleMakeDetailSerializer,
            404: {'description': 'Make not found'},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Vehicles - Makes'],
        summary='Create new make (Owner only)',
        description='Add a new vehicle manufacturer. Owner-only endpoint.',
        request=VehicleMakeSerializer,
        responses={
            201: VehicleMakeSerializer,
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized - owner access required'},
        },
        examples=[
            OpenApiExample(
                'example_make',
                summary='Example vehicle make',
                value={
                    'name': 'Toyota',
                    'country': 'Japan',
                    'logo_url': 'https://example.com/toyota-logo.png',
                    'description': 'Japanese automotive manufacturer',
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Vehicles - Makes'],
        summary='Update make (Owner only)',
        request=VehicleMakeSerializer,
        responses={
            200: VehicleMakeSerializer,
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Make not found'},
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Vehicles - Makes'],
        summary='Delete make (Owner only)',
        responses={
            204: {'description': 'Make deleted'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Make not found'},
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class VehicleModelViewSet(viewsets.ModelViewSet):
    """
    Vehicle models with year compatibility.
    Guest-first: GET is public, POST/PUT/DELETE for owner only.
    """
    queryset = VehicleModel.objects.select_related('make')
    serializer_class = VehicleModelSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['make', 'year_from', 'year_to']
    search_fields = ['name', 'make__name', 'engine_type']
    ordering_fields = ['make__name', 'name', 'year_from']
    ordering = ['make__name', 'name']
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve."""
        if self.action == 'retrieve':
            return VehicleModelDetailSerializer
        return VehicleModelSerializer
    
    @extend_schema(
        tags=['Vehicles - Models'],
        summary='List vehicle models',
        description='Get all vehicle models with optional filtering by make, year range. Public endpoint (no authentication required).',
        parameters=[
            OpenApiParameter(
                name='make',
                description='Filter by make ID',
                required=False,
                type=int,
                location='query',
            ),
            OpenApiParameter(
                name='year_from',
                description='Filter by minimum production year',
                required=False,
                type=int,
                location='query',
            ),
            OpenApiParameter(
                name='year_to',
                description='Filter by maximum production year',
                required=False,
                type=int,
                location='query',
            ),
            OpenApiParameter(
                name='search',
                description='Search by name, make, or engine type',
                required=False,
                type=str,
                location='query',
            ),
        ],
        responses={
            200: VehicleModelSerializer(many=True),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Vehicles - Models'],
        summary='Get model details',
        description='Retrieve a vehicle model with full make information.',
        responses={
            200: VehicleModelDetailSerializer,
            404: {'description': 'Model not found'},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Vehicles - Models'],
        summary='Create new model (Owner only)',
        description='Add a new vehicle model. Owner-only endpoint.',
        request=VehicleModelSerializer,
        responses={
            201: VehicleModelSerializer,
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized - owner access required'},
        },
        examples=[
            OpenApiExample(
                'example_model',
                summary='Example vehicle model',
                value={
                    'make': 1,
                    'name': 'Corolla',
                    'year_from': 2015,
                    'year_to': 2023,
                    'engine_type': '1.6L Petrol',
                    'description': 'Popular sedan model',
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Vehicles - Models'],
        summary='Update model (Owner only)',
        request=VehicleModelSerializer,
        responses={
            200: VehicleModelSerializer,
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Model not found'},
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Vehicles - Models'],
        summary='Delete model (Owner only)',
        responses={
            204: {'description': 'Model deleted'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Model not found'},
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
