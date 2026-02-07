import json
import boto3
import os
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any

dynamodb = boto3.resource('dynamodb')
idempotency_table = dynamodb.Table(os.environ.get('IDEMPOTENCY_TABLE', 'IdempotencyCache'))

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def check_idempotency(request_id: str) -> Optional[Dict[str, Any]]:
    """Check if request was already processed"""
    try:
        response = idempotency_table.get_item(Key={'requestId': request_id})
        if 'Item' in response:
            return json.loads(response['Item']['response'])
        return None
    except Exception as e:
        print(f"Idempotency check error: {str(e)}")
        return None

def store_idempotency(request_id: str, response: Dict[str, Any], ttl_hours: int = 24):
    """Store response for idempotency"""
    try:
        ttl = int((datetime.utcnow() + timedelta(hours=ttl_hours)).timestamp())
        idempotency_table.put_item(Item={
            'requestId': request_id,
            'response': json.dumps(response, default=decimal_default),
            'ttl': ttl,
            'createdAt': datetime.utcnow().isoformat()
        })
    except Exception as e:
        print(f"Idempotency store error: {str(e)}")

def deterministic_hash(input_str: str) -> int:
    """Generate deterministic hash for seeding"""
    return int(hashlib.sha256(input_str.encode()).hexdigest(), 16) % (10 ** 8)

def validate_schema(data: Dict[str, Any], required_fields: list, field_validators: Dict = None) -> tuple[bool, str]:
    """Validate input schema"""
    # Check required fields
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    
    # Run custom validators
    if field_validators:
        for field, validator in field_validators.items():
            if field in data:
                is_valid, error = validator(data[field])
                if not is_valid:
                    return False, f"{field}: {error}"
    
    return True, ""

def validate_guests(value: int) -> tuple[bool, str]:
    """Validate number of guests"""
    if not isinstance(value, int):
        return False, "Must be an integer"
    if not 1 <= value <= 20:
        return False, "Must be between 1 and 20"
    return True, ""

def validate_phone(value: str) -> tuple[bool, str]:
    """Validate phone number format"""
    if not isinstance(value, str):
        return False, "Must be a string"
    cleaned = ''.join(filter(str.isdigit, value))
    if len(cleaned) < 10:
        return False, "Must contain at least 10 digits"
    return True, ""

def validate_amount(value: float) -> tuple[bool, str]:
    """Validate monetary amount"""
    try:
        amount = float(value)
        if amount <= 0:
            return False, "Must be greater than 0"
        if amount > 10000:
            return False, "Exceeds maximum allowed amount"
        return True, ""
    except (ValueError, TypeError):
        return False, "Must be a valid number"
