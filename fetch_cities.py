import boto3
import os
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
table = dynamodb.Table(os.getenv('RESTAURANTS_TABLE', 'Restaurants'))

def fetch_all_cities():
    """Fetch all unique city names from Restaurants table"""
    cities = set()
    
    response = table.scan(ProjectionExpression='city')
    cities.update(item['city'] for item in response['Items'] if 'city' in item)
    
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            ProjectionExpression='city',
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        cities.update(item['city'] for item in response['Items'] if 'city' in item)
    
    return sorted(cities)

if __name__ == '__main__':
    cities = fetch_all_cities()
    print(f"Found {len(cities)} unique cities:")
    for city in cities:
        print(f"  - {city}")
