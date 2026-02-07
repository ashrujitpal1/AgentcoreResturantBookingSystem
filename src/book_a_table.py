import boto3
import os
import uuid
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from utils import check_idempotency, store_idempotency, validate_schema, validate_guests, validate_phone, validate_amount

dynamodb = boto3.resource('dynamodb')
bookings_table = dynamodb.Table(os.environ['BOOKINGS_TABLE'])
restaurants_table = dynamodb.Table(os.environ['RESTAURANTS_TABLE'])
HITL_THRESHOLD = 10

def lambda_handler(event, context):
    """MCP Tool: Book table with idempotency and HITL"""
    try:
        request_id = event.get('requestId')
        if not request_id:
            return {'error': 'requestId is required for idempotency'}
        
        cached = check_idempotency(request_id)
        if cached:
            return cached
        
        is_valid, error = validate_schema(
            event,
            ['restaurantId', 'userName', 'userMobileNo', 'date', 'type', 'cityName', 'noOfGuests', 'tokenAmount'],
            {'noOfGuests': validate_guests, 'userMobileNo': validate_phone, 'tokenAmount': validate_amount}
        )
        if not is_valid:
            return {'error': error}
        
        no_of_guests = int(event['noOfGuests'])
        
        # HITL for large groups
        if no_of_guests > HITL_THRESHOLD:
            result = {
                'requiresApproval': True,
                'message': f'Bookings for more than {HITL_THRESHOLD} guests require manual approval',
                'noOfGuests': no_of_guests
            }
            store_idempotency(request_id, result)
            return result
        
        booking_id = f"booking_{uuid.uuid4().hex[:8]}"
        booking_reference = f"REF{uuid.uuid4().hex[:6].upper()}"
        
        bookings_table.put_item(Item={
            'bookingId': booking_id,
            'restaurantId': event['restaurantId'],
            'userName': event['userName'],
            'userMobileNo': event['userMobileNo'],
            'bookingDate': event['date'],
            'bookingTime': event.get('time', '19:00'),
            'mealType': event['type'],
            'cityName': event['cityName'],
            'noOfGuests': no_of_guests,
            'tokenAmount': Decimal(str(event['tokenAmount'])),
            'bookingStatus': 'confirmed',
            'bookingReference': booking_reference,
            'createdAt': datetime.utcnow().isoformat()
        })
        
        result = {
            'bookingId': booking_id,
            'bookingReference': booking_reference,
            'restaurantId': event['restaurantId'],
            'bookingDate': event['date'],
            'bookingTime': event.get('time', '19:00'),
            'noOfGuests': no_of_guests,
            'message': 'Table booking created successfully'
        }
        
        store_idempotency(request_id, result)
        return result
        
    except Exception as e:
        return {'error': str(e)}
