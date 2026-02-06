"""
M-Pesa / Daraja API utilities.
Handles STK Push, callbacks, and API communication.
"""

import requests
import json
import base64
from django.conf import settings
from datetime import datetime


class DarajaAPI:
    """
    M-Pesa Daraja API wrapper for STK Push.
    Handles authentication and payment initiation.
    """
    
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.business_shortcode = settings.MPESA_BUSINESS_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.environment = settings.MPESA_ENVIRONMENT
        
        # API endpoints
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
    
    def get_access_token(self):
        """
        Get OAuth access token from Daraja API.
        """
        auth_url = f'{self.base_url}/oauth/v1/generate'
        
        response = requests.get(
            auth_url,
            auth=(self.consumer_key, self.consumer_secret),
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            raise Exception(f'Failed to get access token: {response.text}')
    
    def initiate_stk_push(self, phone_number, amount, order_number):
        """
        Initiate M-Pesa STK Push for payment.
        
        Args:
            phone_number (str): Customer phone in format 254712345678
            amount (int): Amount in KSh
            order_number (str): Order number for reference
        
        Returns:
            dict: {
                'success': bool,
                'merchant_request_id': str,
                'checkout_request_id': str,
                'response_code': str,
                'response_message': str,
                'raw_response': dict,
            }
        """
        try:
            access_token = self.get_access_token()
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'raw_response': None,
            }
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Generate password (base64 encoded shortcode+passkey+timestamp)
        password_string = f'{self.business_shortcode}{self.passkey}{timestamp}'
        password = base64.b64encode(password_string.encode()).decode()
        
        # Prepare request
        url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'BusinessShortCode': self.business_shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone_number,
            'PartyB': self.business_shortcode,
            'PhoneNumber': phone_number,
            'CallBackURL': settings.MPESA_CALLBACK_URL,
            'AccountReference': order_number,
            'TransactionDesc': f'AutoParts Order {order_number}',
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'merchant_request_id': response_data.get('MerchantRequestID'),
                    'checkout_request_id': response_data.get('CheckoutRequestID'),
                    'response_code': response_data.get('ResponseCode'),
                    'response_message': response_data.get('ResponseDescription'),
                    'raw_response': response_data,
                }
            else:
                return {
                    'success': False,
                    'response_code': response_data.get('ResponseCode'),
                    'response_message': response_data.get('ResponseDescription'),
                    'raw_response': response_data,
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'raw_response': None,
            }
    
    def validate_callback(self, request_data):
        """
        Validate M-Pesa callback response.
        In production, verify signature. For now, basic validation.
        """
        required_fields = [
            'Body.stkCallback.CheckoutRequestID',
            'Body.stkCallback.ResultCode',
            'Body.stkCallback.ResultDesc',
        ]
        
        # Check if result is successful (ResultCode == 0)
        try:
            result_code = request_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            return result_code == 0
        except (KeyError, TypeError):
            return False
