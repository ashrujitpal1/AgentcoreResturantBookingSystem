import boto3
import os
from decimal import Decimal
from utils import check_idempotency, store_idempotency

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['RESTAURANTS_TABLE'])
CACHE_TTL_HOURS = 1  # 1-hour cache for READ_ONLY queries

def lambda_handler(event, context):
    """MCP Tool: Get restaurant by ID with caching"""
    try:
        # Optional requestId for caching and observability
        request_id = event.get('requestId')
        if request_id:
            cached = check_idempotency(request_id)
            if cached:
                print(f"Returning cached result for requestId: {request_id}")
                return cached
        
        restaurant_id = event.get('restaurantId')
        
        if not restaurant_id:
            return {'error': 'restaurantId is required'}
        
        response = table.get_item(Key={'restaurantId': restaurant_id})
        
        if 'Item' not in response:
            result = {'error': 'Restaurant not found'}
        else:
            result = dict(response['Item'])
        
        # Cache result if requestId provided
        if request_id:
            store_idempotency(request_id, result, ttl_hours=CACHE_TTL_HOURS)
        
        return result
        
    except Exception as e:
        print(f"Error in fetchRestaurantDetailsById: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
