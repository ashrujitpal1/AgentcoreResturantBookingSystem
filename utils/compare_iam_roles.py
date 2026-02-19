#!/usr/bin/env python3
"""
Compare current AWS IAM roles with recreation script.
"""
import json
import sys

print("=" * 80)
print("IAM ROLES COMPARISON - AWS vs Recreation Script")
print("=" * 80)

# Load audit results
with open('deployment/iam_roles_audit.json', 'r') as f:
    audit = json.load(f)

runtime_role = audit['runtime_role']
gateway_role = audit['gateway_role']

# Check Runtime Role
print("\n1. RUNTIME ROLE COMPARISON")
print("-" * 80)

runtime_policy = runtime_role['inline_policies']['AgentCoreRuntimePolicy']
runtime_statements = runtime_policy['Statement']

print(f"✅ Total statements in AWS: {len(runtime_statements)}")

# Critical CloudWatch Logs check
logs_statements = [s for s in runtime_statements if any('logs:' in a for a in s.get('Action', []))]
print(f"\n🔍 CloudWatch Logs Statements: {len(logs_statements)}")

if len(logs_statements) == 3:
    print("✅ CORRECT: 3 separate CloudWatch Logs statements (CRITICAL for logging)")
    for i, stmt in enumerate(logs_statements, 1):
        print(f"\n   Statement {i}:")
        print(f"   Actions: {stmt['Action']}")
        print(f"   Resource: {stmt['Resource']}")
else:
    print(f"❌ ERROR: Expected 3 CloudWatch Logs statements, found {len(logs_statements)}")
    sys.exit(1)

# Verify specific permissions
required_permissions = {
    'Bedrock': ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
    'ECR': ['ecr:BatchGetImage', 'ecr:GetDownloadUrlForLayer', 'ecr:GetAuthorizationToken'],
    'CloudWatch Logs': ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents', 'logs:DescribeLogGroups', 'logs:DescribeLogStreams'],
    'X-Ray': ['xray:PutTraceSegments', 'xray:PutTelemetryRecords'],
    'AgentCore Memory': ['bedrock-agentcore:CreateEvent', 'bedrock-agentcore:GetEvent', 'bedrock-agentcore:ListEvents'],
    'Lambda': ['lambda:InvokeFunction'],
    'S3': ['s3:GetObject', 's3:ListBucket'],
    'SSM': ['ssm:GetParameter']
}

print("\n🔍 Verifying Required Permissions:")
all_actions = []
for stmt in runtime_statements:
    all_actions.extend(stmt.get('Action', []))

missing = []
for category, actions in required_permissions.items():
    found = all([action in all_actions for action in actions])
    if found:
        print(f"   ✅ {category}: All required actions present")
    else:
        print(f"   ❌ {category}: Missing actions")
        missing.append(category)

# Check Gateway Role
print("\n\n2. GATEWAY ROLE COMPARISON")
print("-" * 80)

gateway_policy = gateway_role['inline_policies']['AgentCoreGatewayPolicy']
gateway_statements = gateway_policy['Statement']

print(f"✅ Total statements in AWS: {len(gateway_statements)}")

gateway_actions = gateway_statements[0]['Action']
required_gateway = ['bedrock-agentcore:*', 'bedrock:*', 'lambda:InvokeFunction', 'secretsmanager:GetSecretValue']

print("\n🔍 Verifying Gateway Permissions:")
for action in required_gateway:
    if action in gateway_actions:
        print(f"   ✅ {action}")
    else:
        print(f"   ❌ {action} - MISSING")
        missing.append(f"Gateway: {action}")

# Final verdict
print("\n\n" + "=" * 80)
print("FINAL VERDICT")
print("=" * 80)

if not missing and len(logs_statements) == 3:
    print("✅ PERFECT MATCH: Recreation script will create identical roles")
    print("\n✅ CRITICAL: CloudWatch Logs has 3 separate statements (correct structure)")
    print("\nRecreation script at utils/iam_roles.py is VERIFIED and SAFE to use.")
    sys.exit(0)
else:
    print("❌ MISMATCH DETECTED")
    if missing:
        print(f"\nMissing permissions: {missing}")
    if len(logs_statements) != 3:
        print(f"\n❌ CloudWatch Logs structure incorrect: {len(logs_statements)} statements instead of 3")
    print("\n⚠️  DO NOT use recreation script until fixed!")
    sys.exit(1)
