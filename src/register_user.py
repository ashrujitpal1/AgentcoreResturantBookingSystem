import boto3
import os
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key
from utils import check_idempotency, store_idempotency, validate_phone

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE'])

def lambda_handler(event, context):
    """MCP Tool: Register new user with idempotency"""
    try:
        print(f"Received event: {event}")
        
        request_id = event.get('requestId')
        if request_id:
            cached = check_idempotency(request_id)
            if cached:
                print(f"Returning cached result: {cached}")
                return cached
        
        username = event.get('username')
        mobile_no = event.get('mobileNo')
        user_city = event.get('userCity')
        user_preference = event.get('userPreference', {})
        
        print(f"Parsed params: username={username}, mobile={mobile_no}, city={user_city}")
        
        if not all([username, mobile_no, user_city]):
            return {'error': 'username, mobileNo, and userCity are required'}
        
        is_valid, error = validate_phone(mobile_no)
        if not is_valid:
            return {'error': f'Invalid mobileNo: {error}'}
        
        # Check uniqueness
        response = table.query(
            IndexName='MobileIndex',
            KeyConditionExpression=Key('mobileNo').eq(mobile_no)
        )
        if response['Items']:
            result = {'error': 'User with this mobile number already exists'}
            if request_id:
                store_idempotency(request_id, result)
            return result
        
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        table.put_item(Item={
            'userId': user_id,
            'username': username,
            'mobileNo': mobile_no,
            'userCity': user_city,
            'userPreferences': user_preference,
            'registrationDate': datetime.utcnow().isoformat()
        })
        
        result = {
            'userId': user_id,
            'username': username,
            'message': 'User registered successfully'
        }
        
        print(f"Returning result: {result}")
        
        if request_id:
            store_idempotency(request_id, result)
        
        return result
        
    except Exception as e:
        print(f"Error in registerUser: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
