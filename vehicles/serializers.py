"""
Serializers for vehicle makes and models.
"""

from rest_framework import serializers
from vehicles.models import VehicleMake, VehicleModel


class VehicleMakeSerializer(serializers.ModelSerializer):
    """Vehicle manufacturer serializer."""
    models_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = VehicleMake
        fields = ['id', 'name', 'country', 'logo_url', 'description', 'models_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_models_count(self, obj):
        """Count available models for this make."""
        return obj.models.count()


class VehicleModelSerializer(serializers.ModelSerializer):
    """Vehicle model with make info."""
    make_name = serializers.CharField(source='make.name', read_only=True)
    
    class Meta:
        model = VehicleModel
        fields = [
            'id', 'make', 'make_name', 'name', 'year_from', 'year_to',
            'engine_type', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class VehicleModelDetailSerializer(serializers.ModelSerializer):
    """Detailed vehicle model with full make info."""
    make = VehicleMakeSerializer(read_only=True)
    
    class Meta:
        model = VehicleModel
        fields = [
            'id', 'make', 'name', 'year_from', 'year_to', 'engine_type',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleMakeDetailSerializer(serializers.ModelSerializer):
    """Make with nested models."""
    models = VehicleModelSerializer(many=True, read_only=True)
    
    class Meta:
        model = VehicleMake
        fields = [
            'id', 'name', 'country', 'logo_url', 'description', 'models', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
