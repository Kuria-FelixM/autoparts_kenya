"""
Vehicle compatibility models: makes and models.
Foundation for product compatibility filtering.
"""

from django.db import models


class VehicleMake(models.Model):
    """
    Vehicle manufacturer (e.g., Toyota, Nissan, Hyundai).
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Vehicle manufacturer name'
    )
    
    # Optional: manufacturer country origin
    country = models.CharField(
        max_length=100,
        blank=True,
        help_text='Country of origin (e.g., Japan, South Korea)'
    )
    
    # For display
    logo_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicles_make'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name


class VehicleModel(models.Model):
    """
    Vehicle model (e.g., Corolla, Altima, Tucson).
    Links to VehicleMake.
    Products have ManyToMany to VehicleModel for compatibility.
    """
    make = models.ForeignKey(
        VehicleMake,
        on_delete=models.CASCADE,
        related_name='models'
    )
    
    name = models.CharField(max_length=100)
    
    # Year range for this model generation
    year_from = models.IntegerField(help_text='Start production year')
    year_to = models.IntegerField(help_text='End production year')
    
    # Engine info (optional)
    engine_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g., 1.6L Petrol, 2.0L Diesel'
    )
    
    description = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicles_model'
        unique_together = ['make', 'name', 'year_from', 'year_to']
        ordering = ['make__name', 'name', '-year_from']
        indexes = [
            models.Index(fields=['make', 'name']),
            models.Index(fields=['year_from', 'year_to']),
        ]
    
    def __str__(self):
        return f'{self.make.name} {self.name} ({self.year_from}-{self.year_to})'
    
    def is_compatible_with_year(self, year):
        """
        Check if a specific year is compatible with this model.
        """
        return self.year_from <= year <= self.year_to
