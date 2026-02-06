"""
Utility functions for AutoParts Kenya API.
Includes delivery calculation, Kenyan context helpers, etc.
"""

from datetime import datetime, timedelta
from django.conf import settings
from decimal import Decimal


def calculate_delivery_time(destination_city='Nairobi', delivery_type='standard'):
    """
    Calculate estimated delivery time for Nairobi and East African regions.
    
    Args:
        destination_city (str): City name (default: Nairobi)
        delivery_type (str): 'express' (1-2 days), 'standard' (2-3 days), 'economy' (3-5 days)
    
    Returns:
        dict: {
            'estimated_date': datetime,
            'min_days': int,
            'max_days': int,
            'delivery_base_cost': Decimal,
            'city': str
        }
    """
    delivery_rates = {
        'Nairobi': {'standard': (2, 3), 'express': (1, 1), 'economy': (3, 5)},
        'Kampala': {'standard': (3, 5), 'express': (2, 3), 'economy': (5, 7)},
        'Dar es Salaam': {'standard': (4, 6), 'express': (3, 4), 'economy': (5, 8)},
        'Kigali': {'standard': (4, 7), 'express': (3, 5), 'economy': (6, 10)},
        'Mombasa': {'standard': (2, 4), 'express': (1, 2), 'economy': (4, 6)},
    }
    
    # Default to Nairobi if city not found
    if destination_city not in delivery_rates:
        destination_city = 'Nairobi'
    
    city_rates = delivery_rates[destination_city]
    min_days, max_days = city_rates.get(delivery_type, (2, 3))
    
    # Calculate estimated date (using business days, not weekends)
    today = datetime.now().date()
    estimated_date = today + timedelta(days=min_days)
    
    # Skip weekends
    while estimated_date.weekday() > 4:  # 5 = Saturday, 6 = Sunday
        estimated_date += timedelta(days=1)
    
    return {
        'estimated_date': estimated_date.isoformat(),
        'min_days': min_days,
        'max_days': max_days,
        'delivery_base_cost': Decimal(settings.DELIVERY_BASE_RATE),
        'city': destination_city,
    }


def validate_mpesa_phone_number(phone_number):
    """
    Validate and format phone number for M-Pesa STK Push.
    M-Pesa requires format: 2547XXXXXXXX (no leading +, no 0)
    
    Args:
        phone_number (str): Phone number in any format
    
    Returns:
        str or None: Formatted phone number, or None if invalid
    """
    # Remove spaces, hyphens, etc.
    phone = ''.join(filter(str.isdigit, phone_number))
    
    # Handle different input formats
    if phone.startswith('254'):  # Already in 254... format
        if len(phone) == 12:
            return phone
    elif phone.startswith('0'):  # Kenya 0... format
        phone = '254' + phone[1:]
        if len(phone) == 12:
            return phone
    elif phone.startswith('+254'):  # +254 format
        phone = phone[1:]  # Remove +
        if len(phone) == 12:
            return phone
    
    # Invalid format
    return None


def calculate_order_total_with_delivery(subtotal, destination_city='Nairobi', delivery_type='standard'):
    """
    Calculate total order amount including delivery.
    
    Args:
        subtotal (Decimal): Order subtotal in KSh
        destination_city (str): Destination city
        delivery_type (str): Delivery type
    
    Returns:
        dict: {
            'subtotal': Decimal,
            'delivery_cost': Decimal,
            'total': Decimal,
            'delivery_info': dict (from calculate_delivery_time)
        }
    """
    delivery_info = calculate_delivery_time(destination_city, delivery_type)
    delivery_cost = delivery_info['delivery_base_cost']
    
    subtotal = Decimal(str(subtotal))
    delivery_cost = Decimal(str(delivery_cost))
    
    return {
        'subtotal': subtotal,
        'delivery_cost': delivery_cost,
        'total': subtotal + delivery_cost,
        'delivery_info': delivery_info,
    }


def format_kenyan_currency(amount, include_symbol=True):
    """
    Format amount as Kenyan Shillings.
    
    Args:
        amount (Decimal or int): Amount in KSh
        include_symbol (bool): Include 'KSh' symbol
    
    Returns:
        str: Formatted string (e.g., "KSh 15,000.00")
    """
    amount = Decimal(str(amount))
    formatted = f'{amount:,.2f}'
    if include_symbol:
        return f'KSh {formatted}'
    return formatted


def is_store_owner(user):
    """
    Check if user is the store owner.
    """
    if not user or not user.is_authenticated:
        return False
    return hasattr(user, 'profile') and user.profile.is_owner
