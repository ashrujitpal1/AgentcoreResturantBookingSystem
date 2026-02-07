import boto3
import os
from boto3.dynamodb.conditions import Key
from utils import check_idempotency, store_idempotency

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE'])
CACHE_TTL_HOURS = 1  # 1-hour cache for READ_ONLY queries

def lambda_handler(event, context):
    """MCP Tool: Search user by username or mobile with caching"""
    try:
        # Optional requestId for caching and observability
        request_id = event.get('requestId')
        if request_id:
            cached = check_idempotency(request_id)
            if cached:
                print(f"Returning cached result for requestId: {request_id}")
                return cached
        
        username = event.get('username')
        mobile_no = event.get('userMobileNo')
        
        if not username and not mobile_no:
            return {'error': 'username or userMobileNo is required'}
        
        result = None
        
        # Search by mobile first (more specific)
        if mobile_no:
            response = table.query(
                IndexName='MobileIndex',
                KeyConditionExpression=Key('mobileNo').eq(mobile_no)
            )
            if response['Items']:
                user = response['Items'][0]
                result = {
                    'userId': user.get('userId'),
                    'username': user.get('username'),
                    'mobileNo': user.get('mobileNo'),
                    'userCity': user.get('userCity'),
                    'preferences': user.get('userPreferences', {})
                }
        
        # Search by username if not found
        if not result and username:
            response = table.query(
                IndexName='UsernameIndex',
                KeyConditionExpression=Key('username').eq(username)
            )
            if response['Items']:
                user = response['Items'][0]
                result = {
                    'userId': user.get('userId'),
                    'username': user.get('username'),
                    'mobileNo': user.get('mobileNo'),
                    'userCity': user.get('userCity'),
                    'preferences': user.get('userPreferences', {})
                }
        
        if not result:
            result = {'error': 'User not found'}
        
        # Cache result if requestId provided
        if request_id:
            store_idempotency(request_id, result, ttl_hours=CACHE_TTL_HOURS)
        
        return result
        
    except Exception as e:
        print(f"Error in searchUserDetails: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
