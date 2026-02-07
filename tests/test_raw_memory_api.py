#!/usr/bin/env python3
"""Inspect raw memory API response"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from dotenv import load_dotenv
load_dotenv()

import boto3
import os
import json
import time

memory_client = boto3.client('bedrock-agentcore')
memory_id = os.getenv('MEMORY_ID')

user_id = "raw_api_test"
session_id = "session_raw_" + "x" * 17

# Store an event
print("Storing event...")
import datetime
import base64

params = {"userName": "John", "userMobileNo": "5551234567"}
params_b64 = base64.b64encode(json.dumps(params).encode()).decode()

memory_client.create_event(
    memoryId=memory_id,
    actorId=user_id,
    sessionId=session_id,
    eventTimestamp=datetime.datetime.utcnow().isoformat() + 'Z',
    payload=[
        {'conversational': {'content': {'text': "Book a table"}, 'role': 'USER'}},
        {'conversational': {'content': {'text': "I need more info"}, 'role': 'ASSISTANT'}}
    ],
    metadata={'booking_params_b64': {'stringValue': params_b64}}
)

print("Waiting 5 seconds...")
time.sleep(5)

# Retrieve
print("\nRetrieving...")
response = memory_client.retrieve_memory_records(
    memoryId=memory_id,
    namespace='conversation_history',
    searchCriteria={'searchQuery': user_id},
    maxResults=10
)

print(f"\nResponse keys: {list(response.keys())}")
print(f"\nFull response:")
print(json.dumps(response, indent=2, default=str))
