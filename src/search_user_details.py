import boto3
import os
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE'])

def lambda_handler(event, context):
    """MCP Tool: Search user by username or mobile"""
    try:
        username = event.get('username')
        mobile_no = event.get('userMobileNo')
        
        if not username and not mobile_no:
            return {'error': 'username or userMobileNo is required'}
        
        if mobile_no:
            response = table.query(
                IndexName='MobileIndex',
                KeyConditionExpression=Key('mobileNo').eq(mobile_no)
            )
            if response['Items']:
                user = response['Items'][0]
                return {
                    'userId': user.get('userId'),
                    'username': user.get('username'),
                    'mobileNo': user.get('mobileNo'),
                    'userCity': user.get('userCity'),
                    'preferences': user.get('userPreferences', {})
                }
        
        if username:
            response = table.query(
                IndexName='UsernameIndex',
                KeyConditionExpression=Key('username').eq(username)
            )
            if response['Items']:
                user = response['Items'][0]
                return {
                    'userId': user.get('userId'),
                    'username': user.get('username'),
                    'mobileNo': user.get('mobileNo'),
                    'userCity': user.get('userCity'),
                    'preferences': user.get('userPreferences', {})
                }
        
        return {'error': 'User not found'}
        
    except Exception as e:
        return {'error': str(e)}
