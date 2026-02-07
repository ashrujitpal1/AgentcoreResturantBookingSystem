import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
idempotency_table = dynamodb.Table(os.environ.get('IDEMPOTENCY_TABLE', 'IdempotencyCache'))

CIRCUIT_BREAKER_KEY = 'circuit_breaker_payment'
FAILURE_THRESHOLD = 5
OPEN_DURATION_SECONDS = 60

class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open"""
    pass

def get_circuit_state():
    """Get current circuit breaker state"""
    try:
        response = idempotency_table.get_item(Key={'requestId': CIRCUIT_BREAKER_KEY})
        if 'Item' in response:
            item = response['Item']
            state = item.get('state', 'closed')
            failure_count = int(item.get('failureCount', 0))
            opened_at = item.get('openedAt')
            
            # Check if circuit should be half-open
            if state == 'open' and opened_at:
                opened_time = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))
                if datetime.utcnow() - opened_time.replace(tzinfo=None) > timedelta(seconds=OPEN_DURATION_SECONDS):
                    return 'half-open', 0
            
            return state, failure_count
        return 'closed', 0
    except Exception as e:
        print(f"Circuit breaker state check error: {str(e)}")
        return 'closed', 0

def record_success():
    """Record successful operation"""
    try:
        idempotency_table.put_item(Item={
            'requestId': CIRCUIT_BREAKER_KEY,
            'state': 'closed',
            'failureCount': 0,
            'updatedAt': datetime.utcnow().isoformat()
        })
    except Exception as e:
        print(f"Circuit breaker success record error: {str(e)}")

def record_failure():
    """Record failed operation and potentially open circuit"""
    try:
        state, failure_count = get_circuit_state()
        new_failure_count = failure_count + 1
        
        if new_failure_count >= FAILURE_THRESHOLD:
            # Open circuit
            idempotency_table.put_item(Item={
                'requestId': CIRCUIT_BREAKER_KEY,
                'state': 'open',
                'failureCount': new_failure_count,
                'openedAt': datetime.utcnow().isoformat(),
                'updatedAt': datetime.utcnow().isoformat()
            })
            return 'open'
        else:
            # Increment failure count
            idempotency_table.put_item(Item={
                'requestId': CIRCUIT_BREAKER_KEY,
                'state': 'closed',
                'failureCount': new_failure_count,
                'updatedAt': datetime.utcnow().isoformat()
            })
            return 'closed'
    except Exception as e:
        print(f"Circuit breaker failure record error: {str(e)}")
        return 'closed'

def check_circuit():
    """Check if circuit allows operation"""
    state, _ = get_circuit_state()
    if state == 'open':
        raise CircuitBreakerOpen("Payment service circuit breaker is open. Please try again later.")
    return state
