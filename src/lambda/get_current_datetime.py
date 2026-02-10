import json
from datetime import datetime
import pytz

def lambda_handler(event, context):
    """
    Returns current date and time in multiple formats.
    """
    try:
        # Get timezone from event or default to UTC
        timezone = event.get('timezone', 'UTC')
        
        # Get current datetime
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'currentDate': now.strftime('%Y-%m-%d'),
                'currentTime': now.strftime('%H:%M:%S'),
                'currentDateTime': now.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': now.isoformat(),
                'timezone': timezone,
                'dayOfWeek': now.strftime('%A'),
                'month': now.strftime('%B'),
                'year': now.year
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
