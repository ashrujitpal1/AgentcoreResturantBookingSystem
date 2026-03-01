#!/usr/bin/env python3
"""Test deployed AgentCore Runtime"""
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Get Agent ARN from .env
agent_arn = os.getenv("AGENT_RUNTIME_ARN")
if not agent_arn:
    print("❌ AGENT_RUNTIME_ARN not found in .env")
    exit(1)

print("=" * 80)
print("🧪 TESTING DEPLOYED AGENTCORE RUNTIME")
print("=" * 80)
print(f"Agent ARN: {agent_arn}\n")

client = boto3.client('bedrock-agentcore-control')

def test_query(query: str, user_id: str = "test_user"):
    """Test a query against the deployed agent"""
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    try:
        response = client.invoke_agent(
            agentId=agent_arn.split('/')[-1],
            inputText=query,
            sessionId=f"test_session_{user_id}",
            enableTrace=True
        )
        
        # Parse streaming response
        event_stream = response['completion']
        full_response = ""
        
        for event in event_stream:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    text = chunk['bytes'].decode('utf-8')
                    full_response += text
            elif 'trace' in event:
                print(f"[TRACE] {event['trace']}")
        
        print(f"\n✅ Response:")
        print(full_response)
        
        return full_response
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Run tests
print("\n📋 Test 1: Restaurant Search")
test_query("Find Indian restaurants in New York")

print("\n\n📋 Test 2: Different Cuisine")
test_query("Show me Japanese restaurants")

print("\n\n📋 Test 3: Out of Scope")
test_query("What's the weather today?")

print("\n" + "=" * 80)
print("✅ TESTING COMPLETE")
print("=" * 80)
