"""
User views: registration, profile management, saved vehicles/addresses.
Implements authentication-required endpoints and guest-first philosophy.
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExamples

from core.permissions import IsAuthenticatedOrReadOnly
from users.models import UserProfile, SavedVehicle, SavedAddress
from users.serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserProfileDetailSerializer,
    SavedVehicleSerializer,
    SavedAddressSerializer,
)


class RegistrationView(generics.CreateAPIView):
    """
    User registration endpoint.
    Allows guests to create an account (no authentication required).
    Can also be used for post-purchase account creation: guest → registered user.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Users'],
        summary='Create new user account',
        description='Register a new user account. No authentication required. Can be used for post-purchase account creation.',
        request=UserRegistrationSerializer,
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'user': {'type': 'object'},
                    'profile': {'type': 'object'},
                    'message': {'type': 'string', 'example': 'Account created successfully!'},
                }
            },
            400: {'description': 'Validation error (username/email taken, passwords mismatch, etc.)'},
        },
        examples=[
            OpenApiExamples(
                'example_registration',
                summary='Example registration',
                value={
                    'username': 'john_doe',
                    'email': 'john@example.com',
                    'password': 'SecurePassword123',
                    'password_confirm': 'SecurePassword123',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'phone_number': '+254712345678',
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(
            {
                'user': {
                    'id': result['user'].id,
                    'username': result['user'].username,
                    'email': result['user'].email,
                },
                'profile': UserProfileSerializer(result['profile']).data,
                'message': result['message'],
            },
            status=status.HTTP_201_CREATED
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update authenticated user's profile.
    Only authenticated users can access their profile.
    """
    serializer_class = UserProfileDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Get the authenticated user's profile."""
        user_profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return user_profile
    
    @extend_schema(
        tags=['Users'],
        summary='Get authenticated user profile',
        description='Retrieve the authenticated user\'s profile with saved vehicles and addresses.',
        responses={
            200: UserProfileDetailSerializer,
            401: {'description': 'Unauthorized'},
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users'],
        summary='Update user profile',
        description='Update authenticated user\'s profile settings and preferences.',
        request=UserProfileDetailSerializer,
        responses={
            200: UserProfileDetailSerializer,
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
        },
    )
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class SavedVehicleViewSet(viewsets.ModelViewSet):
    """
    Manage saved vehicles for quick product filtering.
    Only authenticated users can save vehicles.
    """
    serializer_class = SavedVehicleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only return vehicles for authenticated user."""
        return SavedVehicle.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Attach current user to saved vehicle."""
        serializer.save(user=self.request.user)
    
    @extend_schema(
        tags=['Users - Saved Vehicles'],
        summary='List user\'s saved vehicles',
        description='Get all vehicles saved by the authenticated user.',
        responses={
            200: SavedVehicleSerializer(many=True),
            401: {'description': 'Unauthorized'},
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users - Saved Vehicles'],
        summary='Create new saved vehicle',
        description='Save a vehicle for quick product filtering.',
        request=SavedVehicleSerializer,
        responses={
            201: SavedVehicleSerializer,
            400: {'description': 'Validation error (duplicate vehicle)'},
            401: {'description': 'Unauthorized'},
        },
        examples=[
            OpenApiExamples(
                'example_save_vehicle',
                summary='Example saved vehicle',
                value={
                    'make': 'Toyota',
                    'model': 'Corolla',
                    'year': 2020,
                    'nickname': 'My Home Car',
                    'is_primary': True,
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users - Saved Vehicles'],
        summary='Get saved vehicle details',
        responses={
            200: SavedVehicleSerializer,
            404: {'description': 'Vehicle not found'},
            401: {'description': 'Unauthorized'},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users - Saved Vehicles'],
        summary='Update saved vehicle',
        request=SavedVehicleSerializer,
        responses={
            200: SavedVehicleSerializer,
            400: {'description': 'Validation error'},
            404: {'description': 'Vehicle not found'},
            401: {'description': 'Unauthorized'},
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users - Saved Vehicles'],
        summary='Delete saved vehicle',
        responses={
            204: {'description': 'Vehicle deleted'},
            404: {'description': 'Vehicle not found'},
            401: {'description': 'Unauthorized'},
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users - Saved Vehicles'],
        summary='Set as primary vehicle',
        description='Set this vehicle as primary for quick filtering.',
        methods=['POST'],
        responses={
            200: SavedVehicleSerializer,
            404: {'description': 'Vehicle not found'},
            401: {'description': 'Unauthorized'},
        },
    )
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """Set vehicle as primary (only one primary per user)."""
        vehicle = self.get_object()
        SavedVehicle.objects.filter(user=request.user).update(is_primary=False)
        vehicle.is_primary = True
        vehicle.save()
        return Response(SavedVehicleSerializer(vehicle).data)


class SavedAddressViewSet(viewsets.ModelViewSet):
    """
    Manage saved delivery addresses.
    Only authenticated users can save addresses.
    """
    serializer_class = SavedAddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only return addresses for authenticated user."""
        return SavedAddress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Attach current user to address."""
        serializer.save(user=self.request.user)
    
    @extend_schema(
        tags=['Users - Saved Addresses'],
        summary='List user\'s saved addresses',
        description='Get all delivery addresses saved by the authenticated user.',
        responses={
            200: SavedAddressSerializer(many=True),
            401: {'description': 'Unauthorized'},
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users - Saved Addresses'],
        summary='Create new saved address',
        description='Save a delivery address for faster checkout.',
        request=SavedAddressSerializer,
        responses={
            201: SavedAddressSerializer,
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
        },
        examples=[
            OpenApiExamples(
                'example_save_address',
                summary='Example saved address',
                value={
                    'address_type': 'home',
                    'label': 'Home',
                    'street_address': '123 Kenyatta Avenue, Nairobi',
                    'city': 'Nairobi',
                    'postal_code': '00100',
                    'recipient_name': 'John Doe',
                    'recipient_phone': '+254712345678',
                    'is_default': True,
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users - Saved Addresses'],
        summary='Get saved address details',
        responses={
            200: SavedAddressSerializer,
            404: {'description': 'Address not found'},
            401: {'description': 'Unauthorized'},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users - Saved Addresses'],
        summary='Update saved address',
        request=SavedAddressSerializer,
        responses={
            200: SavedAddressSerializer,
            400: {'description': 'Validation error'},
            404: {'description': 'Address not found'},
            401: {'description': 'Unauthorized'},
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users - Saved Addresses'],
        summary='Delete saved address',
        responses={
            204: {'description': 'Address deleted'},
            404: {'description': 'Address not found'},
            401: {'description': 'Unauthorized'},
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users - Saved Addresses'],
        summary='Set as default address',
        description='Set this address as default for quick checkout.',
        methods=['POST'],
        responses={
            200: SavedAddressSerializer,
            404: {'description': 'Address not found'},
            401: {'description': 'Unauthorized'},
        },
    )
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set address as default (only one default per user)."""
        address = self.get_object()
        SavedAddress.objects.filter(user=request.user).update(is_default=False)
        address.is_default = True
        address.save()
        return Response(SavedAddressSerializer(address).data)
