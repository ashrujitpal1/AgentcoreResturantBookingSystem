#!/usr/bin/env python3
"""
Test deployed AgentCore Runtime via Bedrock API
"""
import os
import boto3
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AGENT_RUNTIME_ARN = os.getenv("AGENT_RUNTIME_ARN")

bedrock_runtime = boto3.client("bedrock-agentcore", region_name=AWS_REGION)

def invoke_agent(user_input: str, user_id: str = "test_user_001"):
    """Invoke AgentCore Runtime"""
    session_id = f"test_session_{''.join([str(uuid.uuid4().hex[:8]) for _ in range(4)])}"
    
    print(f"\n📤 Invoking agent...")
    print(f"   User: {user_id}")
    print(f"   Session: {session_id}")
    print(f"   Input: {user_input}")
    
    try:
        payload = {
            "inputText": user_input,
            "userId": user_id,
            "sessionId": session_id
        }
        
        response = bedrock_runtime.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            runtimeSessionId=session_id,
            payload=json.dumps(payload).encode('utf-8')
        )
        
        # Parse streaming response
        output = ""
        for event in response.get("completion", []):
            if "chunk" in event:
                chunk = event["chunk"]
                if "bytes" in chunk:
                    output += chunk["bytes"].decode("utf-8")
        
        print(f"\n✅ Response: {output}")
        return output
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

def test_restaurant_search():
    """Test 1: Restaurant search"""
    print("\n" + "=" * 80)
    print("TEST 1: Restaurant Search (Intent Classification → Restaurant Finder)")
    print("=" * 80)
    
    invoke_agent("Find Italian restaurants in Boston")

def test_booking():
    """Test 2: Booking workflow"""
    print("\n" + "=" * 80)
    print("TEST 2: Booking Workflow (SAGA Pattern)")
    print("=" * 80)
    
    invoke_agent("Book a table for 4 people at restaurant rest_001 tomorrow at 7pm")

def test_user_query():
    """Test 3: User information query"""
    print("\n" + "=" * 80)
    print("TEST 3: User Query")
    print("=" * 80)
    
    invoke_agent("What's my booking history?", user_id="user_001")

if __name__ == "__main__":
    if not AGENT_RUNTIME_ARN:
        print("❌ AGENT_RUNTIME_ARN not found in .env")
        exit(1)
    
    print("\n" + "=" * 80)
    print("TESTING AGENTCORE RUNTIME (STRANDS + LANGGRAPH)")
    print("=" * 80)
    print(f"Agent ARN: {AGENT_RUNTIME_ARN}")
    
    test_restaurant_search()
    test_booking()
    test_user_query()
    
    print("\n" + "=" * 80)
    print("✅ All tests completed")
    print("=" * 80)
