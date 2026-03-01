#!/usr/bin/env python3
import boto3
import json
import uuid
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

runtime_arn = os.getenv("AGENT_RUNTIME_ARN")
if not runtime_arn:
    print("AGENT_RUNTIME_ARN not found in .env")
    sys.exit(1)
client = boto3.client('bedrock-agentcore')

# Test with Indian restaurants in New York (data exists)
test_query = "Find Indian restaurants in New York"
session_id = f"streamlit_test_{uuid.uuid4().hex}"

print(f"🧪 Testing Runtime Endpoint")
print(f"Query: {test_query}")
print(f"Session: {session_id}")
print("=" * 80)

try:
    response = client.invoke_agent_runtime(
        agentRuntimeArn=runtime_arn,
        runtimeSessionId=session_id,
        runtimeUserId="test_user_streamlit",
        payload=json.dumps({"inputText": test_query}).encode('utf-8')
    )
    
    print("\n✅ Invocation successful!")
    print(f"Response keys: {list(response.keys())}")
    
    # Handle both streaming and direct response
    if 'payload' in response:
        for event in response['payload']:
            print(f"Event keys: {list(event.keys())}")
            if 'chunk' in event:
                chunk_data = json.loads(event['chunk']['bytes'].decode('utf-8'))
                print(f"\n📝 Response:\n{chunk_data}")
    else:
        for k, v in response.items():
            if k != 'ResponseMetadata':
                val = v.read().decode('utf-8') if hasattr(v, 'read') else v
                print(f"{k}: {val}")
    
    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
