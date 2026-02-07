import boto3
import os
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['RESTAURANTS_TABLE'])
MAX_RESULTS = 50

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    """MCP Tool: Search restaurants by filters"""
    try:
        city = event.get('city')
        cuisine = event.get('cuisine')
        price_range = event.get('priceRange')
        min_rating = event.get('minRating')
        
        if city:
            response = table.query(
                IndexName='CityIndex',
                KeyConditionExpression=Key('city').eq(city)
            )
        elif cuisine:
            response = table.query(
                IndexName='CuisineIndex',
                KeyConditionExpression=Key('cuisine').eq(cuisine)
            )
        else:
            response = table.scan()
        
        restaurants = response['Items']
        
        # Filter by cuisine if provided
        if cuisine:
            restaurants = [r for r in restaurants if r.get('cuisine', '').lower() == cuisine.lower()]
        
        if price_range:
            restaurants = [r for r in restaurants if r.get('priceRange') == price_range]
        
        if min_rating:
            min_rating_float = float(min_rating)
            restaurants = [r for r in restaurants if float(r.get('rating', 0)) >= min_rating_float]
        
        restaurants.sort(key=lambda x: float(x.get('rating', 0)), reverse=True)
        restaurants = restaurants[:MAX_RESULTS]
        
        return {'restaurants': [dict(r) for r in restaurants]}
        
    except Exception as e:
        return {'error': str(e), 'restaurants': []}
