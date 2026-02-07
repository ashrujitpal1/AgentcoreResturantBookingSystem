import boto3
import os
import uuid
import hashlib
from datetime import datetime
from decimal import Decimal
from utils import check_idempotency, store_idempotency, validate_schema, validate_amount, deterministic_hash
from circuit_breaker import check_circuit, record_success, record_failure, CircuitBreakerOpen

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PAYMENTS_TABLE'])

def process_payment(amount, payment_method, request_id):
    """Deterministic payment simulation"""
    if amount <= 0:
        return False, "Invalid amount"
    if amount > 1000:
        return False, "Amount exceeds limit"
    
    seed = deterministic_hash(request_id)
    if (seed % 100) < 95:
        transaction_id = f"txn_{hashlib.sha256(request_id.encode()).hexdigest()[:12]}"
        return True, transaction_id
    return False, "Payment processing failed"

def lambda_handler(event, context):
    """MCP Tool: Process payment with idempotency and circuit breaker"""
    try:
        request_id = event.get('requestId')
        if not request_id:
            return {'error': 'requestId is required for idempotency'}
        
        cached = check_idempotency(request_id)
        if cached:
            return cached
        
        try:
            check_circuit()
        except CircuitBreakerOpen as e:
            result = {'error': str(e), 'paymentStatus': 'circuit_open'}
            store_idempotency(request_id, result)
            return result
        
        is_valid, error = validate_schema(
            event,
            ['userId', 'restaurantId', 'tokenAmount'],
            {'tokenAmount': validate_amount}
        )
        if not is_valid:
            return {'error': error}
        
        token_amount = Decimal(str(event['tokenAmount']))
        payment_method = event.get('paymentMethod', 'credit_card')
        
        success, transaction_result = process_payment(float(token_amount), payment_method, request_id)
        
        if not success:
            record_failure()
            result = {'error': f'Payment failed: {transaction_result}', 'paymentStatus': 'failed'}
            store_idempotency(request_id, result)
            return result
        
        payment_id = f"pay_{uuid.uuid4().hex[:8]}"
        table.put_item(Item={
            'paymentId': payment_id,
            'bookingId': event.get('bookingId', ''),
            'userId': event['userId'],
            'restaurantId': event['restaurantId'],
            'amount': token_amount,
            'paymentMethod': payment_method,
            'paymentStatus': 'completed',
            'transactionId': transaction_result,
            'paymentDate': datetime.utcnow().isoformat()
        })
        
        record_success()
        
        result = {
            'paymentId': payment_id,
            'transactionId': transaction_result,
            'amount': float(token_amount),  # Convert Decimal to float for JSON
            'paymentStatus': 'completed',
            'paymentDate': datetime.utcnow().isoformat()
        }
        
        store_idempotency(request_id, result)
        return result
        
    except Exception as e:
        return {'error': str(e)}
