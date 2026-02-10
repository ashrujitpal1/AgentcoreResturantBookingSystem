#!/usr/bin/env python3
"""Deploy CloudWatch monitoring for production."""
import boto3
import json

cloudwatch = boto3.client('cloudwatch')

# Create alarms
alarms = [
    {
        "AlarmName": "RestaurantBooking-HighErrorRate",
        "MetricName": "Errors",
        "Namespace": "AWS/Lambda",
        "Statistic": "Sum",
        "Period": 300,
        "EvaluationPeriods": 2,
        "Threshold": 10,
        "ComparisonOperator": "GreaterThanThreshold"
    }
]

for alarm in alarms:
    cloudwatch.put_metric_alarm(**alarm)
    print(f"✅ Created alarm: {alarm['AlarmName']}")
