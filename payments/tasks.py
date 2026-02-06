"""
Celery tasks for payment processing.
Handles async M-Pesa callback processing and notifications.
"""

from celery import shared_task
from django.utils.timezone import now
import logging
from orders.models import Order
from payments.models import TransactionLog

logger = logging.getLogger(__name__)


@shared_task
def process_mpesa_callback(callback_data):
    """
    Process M-Pesa STK Push callback asynchronously.
    Updates order status based on payment result.
    """
    try:
        # Extract data
        body = callback_data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc', '')
        
        # Find transaction log
        try:
            transaction = TransactionLog.objects.get(checkout_request_id=checkout_request_id)
            order = transaction.order
        except TransactionLog.DoesNotExist:
            logger.error(f'Transaction not found for CheckoutRequestID: {checkout_request_id}')
            return
        
        # Handle result
        if result_code == 0:
            # Payment successful
            item_data = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            mpesa_receipt = ''
            amount = 0
            
            # Extract receipt and amount
            for item in item_data:
                if item.get('Name') == 'MpesaReceiptNumber':
                    mpesa_receipt = item.get('Value', '')
                elif item.get('Name') == 'Amount':
                    amount = item.get('Value', 0)
            
            # Update order
            order.payment_status = 'paid'
            order.order_status = 'confirmed'
            order.paid_at = now()
            order.save()
            
            # Update transaction log
            transaction.transaction_type = 'payment_success'
            transaction.mpesa_receipt = mpesa_receipt
            transaction.response_code = '0'
            transaction.response_description = 'Payment successful'
            transaction.raw_response = callback_data
            transaction.save()
            
            logger.info(f'Payment successful: Order {order.order_number}, Receipt: {mpesa_receipt}')
            
            # TODO: Send confirmation email/SMS to customer
            # send_payment_confirmation.delay(order.id)
        
        elif result_code == 1:
            # User cancelled
            transaction.transaction_type = 'user_cancel'
            transaction.raw_response = callback_data
            transaction.save()
            
            order.payment_status = 'unpaid'
            order.save()
            
            logger.info(f'User cancelled STK: Order {order.order_number}')
        
        else:
            # Other error
            transaction.transaction_type = 'payment_failed'
            transaction.response_code = str(result_code)
            transaction.response_description = result_desc
            transaction.raw_response = callback_data
            transaction.save()
            
            order.payment_status = 'failed'
            order.save()
            
            logger.warning(f'Payment failed: Order {order.order_number}, Code: {result_code}, Desc: {result_desc}')
    
    except Exception as e:
        logger.error(f'Error processing M-Pesa callback: {str(e)}', exc_info=True)
        raise
