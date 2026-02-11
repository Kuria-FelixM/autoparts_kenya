"""
Payment views: M-Pesa STK Push initiation and callbacks.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import logging

from orders.models import Order
from payments.models import TransactionLog
from payments.utils import DarajaAPI
from payments.serializers import STKPushSerializer, CallbackSerializer
from payments.tasks import process_mpesa_callback
from core.utils import validate_mpesa_phone_number

logger = logging.getLogger(__name__)


class STKPushInitiateView(generics.CreateAPIView):
    """
    Initiate M-Pesa STK Push for order payment.
    Only authenticated or guest users who just placed an order.
    """
    serializer_class = STKPushSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Payments'],
        summary='Initiate M-Pesa STK Push',
        description='Start M-Pesa STK Push payment for an order. Can provide phone or use from order.',
        request=STKPushSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'merchant_request_id': {'type': 'string'},
                    'checkout_request_id': {'type': 'string'},
                    'response_message': {'type': 'string'},
                    'message': {'type': 'string', 'example': 'STK Push sent to phone. Please check your phone and enter PIN.'},
                }
            },
            400: {'description': 'Invalid order or phone number'},
            404: {'description': 'Order not found'},
        },
        examples=[
            OpenApiExample(
                'example_stk_push',
                summary='Example STK Push initiation',
                value={
                    'order_id': 1,
                    'phone_number': '+254712345678',
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data.get('order_id')
        phone_number = serializer.validated_data.get('phone_number')
        
        # Get order
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Agizo halijulikani. (Order not found.)'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get phone number from request or order
        if not phone_number:
            phone_number = order.recipient_phone
        
        # Validate and format phone
        phone_number = validate_mpesa_phone_number(phone_number)
        if not phone_number:
            return Response(
                {'error': 'Namba ya simu si sahihi. (Invalid phone number.)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initiate STK Push
        daraja = DarajaAPI()
        result = daraja.initiate_stk_push(
            phone_number=phone_number,
            amount=order.total_amount,
            order_number=order.order_number
        )
        
        # Log transaction
        if result.get('success'):
            TransactionLog.objects.create(
                order=order,
                transaction_type='stk_initiate',
                merchant_request_id=result.get('merchant_request_id', ''),
                checkout_request_id=result.get('checkout_request_id', ''),
                phone_number=phone_number,
                amount=order.total_amount,
                response_code=result.get('response_code', '0'),
                response_description=result.get('response_message', ''),
                raw_response=result.get('raw_response'),
            )
            
            return Response(
                {
                    'success': True,
                    'merchant_request_id': result.get('merchant_request_id'),
                    'checkout_request_id': result.get('checkout_request_id'),
                    'response_message': result.get('response_message'),
                    'message': 'STK Push imetumwa simu. Tafadhali angalia simu na ingiza PIN. (STK Push sent. Check your phone and enter PIN.)',
                },
                status=status.HTTP_200_OK
            )
        else:
            # Log failed attempt
            TransactionLog.objects.create(
                order=order,
                transaction_type='stk_initiate',
                phone_number=phone_number,
                amount=order.total_amount,
                response_code=result.get('response_code', 'ERROR'),
                response_description=result.get('response_message', result.get('error', 'Unknown error')),
                raw_response=result.get('raw_response'),
            )
            
            return Response(
                {
                    'success': False,
                    'error': result.get('response_message') or result.get('error'),
                    'message': 'Haliwezi kuanza malipo. Jaribu tena. (Could not initiate payment. Try again.)',
                },
                status=status.HTTP_400_BAD_REQUEST
            )


@csrf_exempt  # M-Pesa callback doesn't include CSRF token
@api_view(['POST'])
@permission_classes([AllowAny])
@extend_schema(
    tags=['Payments'],
    summary='M-Pesa callback webhook',
    description='Webhook endpoint for M-Pesa payment confirmations. Called by Safaricom after STK Push confirmation.',
    request=CallbackSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'ResultCode': {'type': 'integer', 'example': 0},
                'ResultDesc': {'type': 'string', 'example': 'The service request has been accepted for processing'},
            }
        },
    },
)
def mpesa_callback_webhook(request):
    """
    M-Pesa callback webhook.
    Receives payment confirmation from Safaricom and updates order status.
    Processes asynchronously via Celery to avoid timeout.
    """
    try:
        # Parse callback data
        if request.content_type == 'application/json':
            callback_data = json.loads(request.body)
        else:
            callback_data = request.POST.dict()
        
        # Log raw callback
        logger.info(f'M-Pesa Callback: {json.dumps(callback_data, indent=2)}')
        
        # Extract key data
        body = callback_data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        
        # Queue async processing
        if checkout_request_id:
            process_mpesa_callback.delay(callback_data)
        
        # Return success to M-Pesa (must respond quickly)
        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'The service request has been accepted for processing',
        })
    
    except Exception as e:
        logger.error(f'M-Pesa callback error: {str(e)}')
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': 'Error processing callback',
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@extend_schema(
    tags=['Payments'],
    summary='Check payment status',
    description='Check payment status for an order.',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'order_id': {'type': 'integer'},
                'order_number': {'type': 'string'},
                'payment_status': {'type': 'string'},
                'order_status': {'type': 'string'},
                'total_amount': {'type': 'string'},
            }
        },
    },
)
def check_payment_status(request):
    """Check payment status for user's order."""
    order_id = request.query_params.get('order_id')
    
    if not order_id:
        return Response(
            {'error': 'order_id parameter required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response(
            {'error': 'Agizo halijulikani.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response({
        'order_id': order.id,
        'order_number': order.order_number,
        'payment_status': order.payment_status,
        'order_status': order.order_status,
        'total_amount': float(order.total_amount),
        'paid_at': order.paid_at,
    })
