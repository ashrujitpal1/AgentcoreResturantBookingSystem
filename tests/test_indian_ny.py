#!/usr/bin/env python3
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client('bedrock-agentcore')
runtime_arn = os.getenv("AGENT_RUNTIME_ARN")

print("Testing: Find Indian restaurants in New York")

response = client.invoke_agent_runtime(
    agentRuntimeArn=runtime_arn,
    runtimeSessionId=f"test_indian_{'x' * 25}",
    runtimeUserId="test_user",
    payload=json.dumps({"inputText": "Find Indian restaurants in New York"}).encode('utf-8')
)

for event in response['payload']:
    if 'chunk' in event:
        data = json.loads(event['chunk']['bytes'].decode('utf-8'))
        if 'response' in data:
            print(f"\nResponse:\n{data['response']}")
