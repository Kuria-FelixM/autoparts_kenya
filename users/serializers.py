"""
Serializers for user registration, profile, saved vehicles, and addresses.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from users.models import UserProfile, SavedVehicle, SavedAddress


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile with extended info."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'is_owner', 'phone_number', 'avatar_url', 'bio',
            'business_registration', 'tax_id', 'email_notifications',
            'sms_notifications', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'is_owner', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.Serializer):
    """
    User registration endpoint.
    Creates User + UserProfile in one request.
    Post-purchase account creation: guests can convert to registered users.
    """
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate passwords match."""
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError(
                {'password': 'Nywila hazisambani. (Passwords do not match.)'}
            )
        
        # Check if username exists
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError(
                {'username': 'Jina hili tayari linatumika. (This username is already taken.)'}
            )
        
        # Check if email exists
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                {'email': 'Barua hii tayari imesajiliwa. (This email is already registered.)'}
            )
        
        return data
    
    def create(self, validated_data):
        """Create User and UserProfile."""
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        
        # Create profile
        profile = UserProfile.objects.create(
            user=user,
            phone_number=validated_data.get('phone_number', ''),
        )
        
        return {
            'user': user,
            'profile': profile,
            'message': 'Akaunti imeundwa kwa mafanikio! (Account created successfully!)'
        }


class SavedVehicleSerializer(serializers.ModelSerializer):
    """Saved vehicle for product filtering."""
    class Meta:
        model = SavedVehicle
        fields = ['id', 'make', 'model', 'year', 'nickname', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']


class SavedAddressSerializer(serializers.ModelSerializer):
    """Saved delivery address."""
    class Meta:
        model = SavedAddress
        fields = [
            'id', 'address_type', 'label', 'street_address', 'city', 'postal_code',
            'recipient_name', 'recipient_phone', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """Full user profile with saved vehicles and addresses."""
    user = UserSerializer(read_only=True)
    saved_vehicles = SavedVehicleSerializer(many=True, read_only=True, source='user.saved_vehicles')
    saved_addresses = SavedAddressSerializer(many=True, read_only=True, source='user.saved_addresses')
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'is_owner', 'phone_number', 'avatar_url', 'bio',
            'email_notifications', 'sms_notifications', 'saved_vehicles',
            'saved_addresses', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'is_owner', 'created_at', 'updated_at']
