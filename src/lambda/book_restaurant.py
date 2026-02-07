import boto3
import os
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['BOOKINGS_TABLE'])

def lambda_handler(event, context):
    """MCP Tool: Simple booking (legacy/alternative)"""
    try:
        restaurant_id = event.get('restaurantId')
        user_id = event.get('userId')
        booking_date = event.get('bookingDate')
        booking_time = event.get('bookingTime')
        no_of_guests = event.get('numberOfGuests', 2)
        
        if not all([restaurant_id, user_id, booking_date, booking_time]):
            return {'error': 'restaurantId, userId, bookingDate, and bookingTime are required'}
        
        booking_id = f"booking_{uuid.uuid4().hex[:8]}"
        
        table.put_item(Item={
            'bookingId': booking_id,
            'restaurantId': restaurant_id,
            'userId': user_id,
            'bookingDate': booking_date,
            'bookingTime': booking_time,
            'noOfGuests': int(no_of_guests),
            'bookingStatus': 'confirmed',
            'createdAt': datetime.utcnow().isoformat()
        })
        
        return {
            'bookingId': booking_id,
            'restaurantId': restaurant_id,
            'bookingDate': booking_date,
            'bookingTime': booking_time,
            'message': 'Booking created successfully'
        }
        
    except Exception as e:
        return {'error': str(e)}
