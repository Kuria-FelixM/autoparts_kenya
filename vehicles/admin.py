"""
Django admin configuration for vehicle models.
Enables manual creation and management of vehicle makes and models.
"""

from django.contrib import admin
from .models import VehicleMake, VehicleModel


@admin.register(VehicleMake)
class VehicleMakeAdmin(admin.ModelAdmin):
    """
    Admin interface for VehicleMake (e.g., Toyota, Nissan, Hyundai).
    """
    list_display = ['name', 'country', 'created_at']
    search_fields = ['name', 'country']
    list_filter = ['country', 'created_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'country')
        }),
        ('Display & Branding', {
            'fields': ('logo_url', 'description'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    """
    Admin interface for VehicleModel (e.g., Corolla, Altima, Tucson).
    Supports filtering by make and year range.
    """
    list_display = ['__str__', 'make', 'year_range', 'engine_type', 'created_at']
    search_fields = ['name', 'make__name', 'engine_type']
    list_filter = ['make', 'year_from', 'created_at']
    ordering = ['make__name', 'name', '-year_from']
    
    fieldsets = (
        ('Vehicle Information', {
            'fields': ('make', 'name')
        }),
        ('Production Years', {
            'fields': ('year_from', 'year_to'),
            'description': 'Enter the production year range for this model generation'
        }),
        ('Engine Details', {
            'fields': ('engine_type', 'description'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def year_range(self, obj):
        """Display year range in list view."""
        return f'{obj.year_from} - {obj.year_to}'
    year_range.short_description = 'Years'
