#!/usr/bin/env python3
"""Test list_events API"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from dotenv import load_dotenv
load_dotenv()

import boto3
import os
import json

memory_client = boto3.client('bedrock-agentcore')
memory_id = os.getenv('MEMORY_ID')

user_id = "raw_api_test"

# Try list_events
print("Listing events...")
try:
    response = memory_client.list_events(
        memoryId=memory_id,
        actorId=user_id,
        maxResults=10
    )
    
    print(f"\nResponse keys: {list(response.keys())}") 
    print(f"\nFull response:")
    print(json.dumps(response, indent=2, default=str))
except Exception as e:
    print(f"Error: {e}")
