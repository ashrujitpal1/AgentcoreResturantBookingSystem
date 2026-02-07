import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['RESTAURANTS_TABLE'])

def lambda_handler(event, context):
    """MCP Tool: Get restaurant by ID"""
    try:
        restaurant_id = event.get('restaurantId')
        
        if not restaurant_id:
            return {'error': 'restaurantId is required'}
        
        response = table.get_item(Key={'restaurantId': restaurant_id})
        
        if 'Item' not in response:
            return {'error': 'Restaurant not found'}
        
        return dict(response['Item'])
        
    except Exception as e:
        return {'error': str(e)}
