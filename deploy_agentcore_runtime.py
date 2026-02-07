#!/usr/bin/env python3
"""
Deploy AgentCore Runtime with Strands + LangGraph workflow.
Follows agentcore-for-education pattern with proper IAM role creation.
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
from utils.iam_roles import create_agentcore_runtime_role
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

boto_session = Session()
region = boto_session.region_name
account_id = boto_session.client("sts").get_caller_identity()["Account"]

print("=" * 80)
print("DEPLOYING AGENTCORE RUNTIME (STRANDS + LANGGRAPH)")
print("=" * 80)
print(f"Region: {region}")
print(f"Account: {account_id}")

# Step 1: Create IAM role with CloudWatch Logs permissions
print("\n📋 Step 1: Creating IAM role with CloudWatch Logs permissions...")
agentcore_runtime_role = create_agentcore_runtime_role("restaurant_booking")
role_arn = agentcore_runtime_role['Role']['Arn']
print(f"✅ Role ARN: {role_arn}")

# Step 2: Get Memory ID from environment
memory_id = os.getenv("MEMORY_ID")
if not memory_id:
    raise ValueError("MEMORY_ID not found in .env file. Run: python3 deploy_agentcore_memory.py")

print(f"\n✅ Using MEMORY_ID: {memory_id}")

# Step 3: Configure AgentCore Runtime
print("\n📦 Step 3: Configuring AgentCore Runtime...")
agentcore_runtime = Runtime()
agent_name = "restaurant_booking_orchestrator"

response = agentcore_runtime.configure(
    entrypoint="src/orchestrator.py",
    execution_role=role_arn,
    auto_create_ecr=True,
    requirements_file="requirements.txt",
    region=region,
    agent_name=agent_name
)

print("✅ Configuration successful!")
print(response)

# Step 4: Launch AgentCore Runtime
print("\n🚀 Step 4: Launching agent...")

# Pass environment variables to runtime
env_vars = {
    "MEMORY_ID": memory_id,
    "AWS_REGION": region
}

launch_result = agentcore_runtime.launch(
    auto_update_on_conflict=True,
    env_vars=env_vars
)

print("\n✅ Launch successful!")
print(f"Launch result type: {type(launch_result)}")
print(launch_result)

# Step 5: Save Agent ID
if hasattr(launch_result, 'agent_id'):
    agent_id = launch_result.agent_id
    os.makedirs("deployment", exist_ok=True)
    with open("deployment/agent_id.txt", "w") as f:
        f.write(agent_id)
    print(f"\n📝 Agent ID saved: {agent_id}")

# Step 6: Save Agent Runtime ARN to .env
if hasattr(launch_result, 'agent_arn'):
    agent_runtime_arn = launch_result.agent_arn
    print(f"\n🎯 Agent ARN: {agent_runtime_arn}")
    
    # Update .env file
    env_file_path = '.env'
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            lines = f.readlines()
        
        updated_lines = []
        arn_updated = False
        
        for line in lines:
            if line.startswith('AGENT_RUNTIME_ARN'):
                updated_lines.append(f'AGENT_RUNTIME_ARN={agent_runtime_arn}\n')
                arn_updated = True
            else:
                updated_lines.append(line)
        
        if not arn_updated:
            updated_lines.append(f'AGENT_RUNTIME_ARN={agent_runtime_arn}\n')
        
        with open(env_file_path, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ .env file updated with AGENT_RUNTIME_ARN")
    else:
        print("⚠️  .env file not found, please add AGENT_RUNTIME_ARN manually")
else:
    print("❌ Agent Runtime ARN not found in launch_result")
    print("Available attributes:", [attr for attr in dir(launch_result) if not attr.startswith('_')])

print("\n" + "=" * 80)
print("✅ DEPLOYMENT COMPLETE")
print("=" * 80)
print("\nNext steps:")
print("1. Check CloudWatch Logs: /aws/bedrock-agentcore/runtimes/<runtime-id>")
print("2. Test with: python3 tests/test_orchestrator.py")
print("3. Invoke via Bedrock: aws bedrock-agentcore-runtime invoke-agent")
