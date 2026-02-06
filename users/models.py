"""
User models: authentication, profiles, saved vehicles, addresses.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator, RegexValidator
from django.core.exceptions import ValidationError


class UserProfile(models.Model):
    """
    Extended user profile with store owner flag and customer preferences.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Store owner identification (guest-first design)
    is_owner = models.BooleanField(
        default=False,
        help_text='Only one user should have this enabled in production.'
    )
    
    # Profile details
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^(\+?254|0)?[1-9]\d{1,9}$',
                message='Namba ya simu si sahihi. (Invalid phone number format.)',
            )
        ]
    )
    
    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    
    # Business info (for store owner)
    business_registration = models.CharField(max_length=50, blank=True, help_text='Store registration number')
    tax_id = models.CharField(max_length=50, blank=True, help_text='KRA PIN or similar')
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_profile'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_owner']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} (Owner: {self.is_owner})'


class SavedVehicle(models.Model):
    """
    Vehicles saved by user for quick product filtering.
    Supports guest checkout but authenticated users can save for quick reuse.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_vehicles')
    
    # Vehicle info
    make = models.CharField(max_length=50, help_text='e.g., Toyota, Nissan')
    model = models.CharField(max_length=100, help_text='e.g., Corolla, Altima')
    year = models.IntegerField(help_text='Manufacturing year')
    
    # User's nickname for this vehicle
    nickname = models.CharField(max_length=50, blank=True, help_text='e.g., My Home Car')
    
    # Metadata
    is_primary = models.BooleanField(default=False, help_text='Primary vehicle for quick filter')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users_saved_vehicle'
        unique_together = ['user', 'make', 'model', 'year']  # No duplicate vehicles per user
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_primary']),
        ]
    
    def __str__(self):
        return f'{self.year} {self.make} {self.model} - {self.user.username}'


class SavedAddress(models.Model):
    """
    Saved delivery addresses for faster checkout.
    """
    ADDRESS_TYPES = [
        ('home', 'Nyumbani (Home)'),
        ('work', 'Kazi (Work)'),
        ('other', 'Nyingine (Other)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_addresses')
    
    # Address details
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='home')
    label = models.CharField(max_length=100, help_text='Display name for address')
    
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Contact for this address
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^(\+?254|0)?[1-9]\d{1,9}$',
                message='Invalid phone number format.',
            )
        ]
    )
    
    # Metadata
    is_default = models.BooleanField(default=False, help_text='Use as default delivery address')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_saved_address'
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),
        ]
    
    def __str__(self):
        return f'{self.label} - {self.user.username}'
    
    def save(self, *args, **kwargs):
        """Ensure only one default address per user."""
        if self.is_default:
            SavedAddress.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
