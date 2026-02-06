"""
Payment serializers.
"""

from rest_framework import serializers


class STKPushSerializer(serializers.Serializer):
    """Request serializer for STK Push initiation."""
    order_id = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=15, required=False)
    
    def validate_phone_number(self, value):
        """Validate M-Pesa phone format."""
        from core.utils import validate_mpesa_phone_number
        if value:
            formatted = validate_mpesa_phone_number(value)
            if not formatted:
                raise serializers.ValidationError('Namba ya simu si sahihi. (Invalid phone number.)')
            return formatted
        return value


class CallbackSerializer(serializers.Serializer):
    """M-Pesa callback response serializer."""
    Body = serializers.JSONField()
