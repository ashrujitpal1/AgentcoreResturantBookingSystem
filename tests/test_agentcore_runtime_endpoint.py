#!/usr/bin/env python3
"""Test AgentCore Runtime endpoint directly"""
import boto3
import json
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

AGENT_RUNTIME_ARN = os.getenv("AGENT_RUNTIME_ARN")
if not AGENT_RUNTIME_ARN:
    print("❌ AGENT_RUNTIME_ARN not found in .env")
    sys.exit(1)

print(f"🎯 Testing AgentCore Runtime: {AGENT_RUNTIME_ARN}")
print("=" * 80)

# Create client
client = boto3.client('bedrock-agentcore')

# Test query
test_query = "Find Indian restaurants in New York"
session_id = f"test_session_{'x' * 25}"  # 38 chars total
user_id = "test_user_123"

print(f"\n📝 Query: {test_query}")
print(f"👤 User ID: {user_id}")
print(f"🔑 Session ID: {session_id} (length: {len(session_id)})")
print("\n🚀 Invoking runtime...\n")

try:
    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        runtimeSessionId=session_id,
        runtimeUserId=user_id,
        payload=json.dumps({
            "inputText": test_query
        }).encode('utf-8')
    )
    
    print("✅ Response received!")
    print(f"Response keys: {response.keys()}")
    
    # Parse streaming response
    if 'payload' in response:
        print("\n📦 Processing payload stream...")
        for event in response['payload']:
            print(f"Event type: {list(event.keys())}")
            
            if 'chunk' in event:
                chunk_bytes = event['chunk']['bytes']
                chunk_data = json.loads(chunk_bytes.decode('utf-8'))
                print(f"\n📄 Chunk data keys: {chunk_data.keys()}")
                print(f"\n💬 Response:\n{json.dumps(chunk_data, indent=2)}")
                
                if 'response' in chunk_data:
                    print(f"\n✅ Final Response:\n{chunk_data['response']}")
                    
            elif 'internalServerException' in event:
                print(f"\n❌ Internal Server Error: {event['internalServerException']}")
                
            elif 'validationException' in event:
                print(f"\n❌ Validation Error: {event['validationException']}")
    
    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    
    print("\n💡 Checking CloudWatch logs...")
    print(f"Run: aws logs tail /aws/bedrock-agentcore/runtimes/restaurant_booking_orchestrator-JZpyQwCgEq --follow")
