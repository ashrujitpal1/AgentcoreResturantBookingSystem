import boto3
import os
import json
import base64
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from utils import check_idempotency, store_idempotency

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['RESTAURANTS_TABLE'])
MAX_RESULTS = 50
CACHE_TTL_HOURS = 1  # 1-hour cache for READ_ONLY queries

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def truncate_restaurant(restaurant):
    """Truncate large fields to prevent payload size issues"""
    MAX_DESCRIPTION_LENGTH = 500
    MAX_MENU_ITEMS = 20
    
    if 'description' in restaurant and len(restaurant['description']) > MAX_DESCRIPTION_LENGTH:
        restaurant['description'] = restaurant['description'][:MAX_DESCRIPTION_LENGTH] + '...'
    
    if 'menuCard' in restaurant and isinstance(restaurant['menuCard'], list):
        restaurant['menuCard'] = restaurant['menuCard'][:MAX_MENU_ITEMS]
    
    return restaurant

def lambda_handler(event, context):
    """MCP Tool: Search restaurants by filters with pagination and caching"""
    try:
        # Optional requestId for caching and observability
        request_id = event.get('requestId')
        if request_id:
            cached = check_idempotency(request_id)
            if cached:
                print(f"Returning cached result for requestId: {request_id}")
                return cached
        
        city = event.get('city')
        cuisine = event.get('cuisine')
        price_range = event.get('priceRange')
        min_rating = event.get('minRating')
        max_results = min(int(event.get('maxResults', MAX_RESULTS)), 100)
        next_token = event.get('nextToken')
        
        # Build query/scan with pagination
        scan_kwargs = {'Limit': max_results}
        
        if next_token:
            try:
                scan_kwargs['ExclusiveStartKey'] = json.loads(base64.b64decode(next_token).decode('utf-8'))
            except Exception as e:
                print(f"Invalid nextToken: {e}")
        
        # Use index if available
        if city:
            scan_kwargs['IndexName'] = 'CityIndex'
            scan_kwargs['KeyConditionExpression'] = Key('city').eq(city)
            response = table.query(**scan_kwargs)
        else:
            response = table.scan(**scan_kwargs)
        
        restaurants = response['Items']
        
        # Apply filters
        if cuisine:
            restaurants = [r for r in restaurants if r.get('cuisine', '').lower() == cuisine.lower()]
        
        if price_range:
            restaurants = [r for r in restaurants if r.get('priceRange') == price_range]
        
        if min_rating:
            min_rating_float = float(min_rating)
            restaurants = [r for r in restaurants if float(r.get('rating', 0)) >= min_rating_float]
        
        # Deduplicate by name+city (keep highest rated)
        seen = {}
        for r in restaurants:
            key = f"{r.get('name', '')}_{r.get('city', '')}"
            if key not in seen or float(r.get('rating', 0)) > float(seen[key].get('rating', 0)):
                seen[key] = r
        restaurants = list(seen.values())
        
        # Sort by rating
        restaurants.sort(key=lambda x: float(x.get('rating', 0)), reverse=True)
        
        # Truncate large fields
        restaurants = [truncate_restaurant(dict(r)) for r in restaurants[:max_results]]
        
        # Build result with pagination
        result = {'restaurants': restaurants}
        
        if 'LastEvaluatedKey' in response:
            result['nextToken'] = base64.b64encode(
                json.dumps(response['LastEvaluatedKey'], default=decimal_default).encode('utf-8')
            ).decode('utf-8')
        
        # Cache result if requestId provided
        if request_id:
            store_idempotency(request_id, result, ttl_hours=CACHE_TTL_HOURS)
        
        return result
        
    except Exception as e:
        print(f"Error in fetchRestaurantDetails: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e), 'restaurants': []}
