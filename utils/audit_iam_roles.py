#!/usr/bin/env python3
"""
Audit IAM roles - Retrieve current roles from AWS and compare with recreation script.
"""
import boto3
import json
from botocore.exceptions import ClientError

iam = boto3.client('iam')

def get_role_details(role_name):
    """Retrieve role and its policies from AWS"""
    try:
        # Get role
        role_response = iam.get_role(RoleName=role_name)
        role = role_response['Role']
        
        # Get inline policies
        policies_response = iam.list_role_policies(RoleName=role_name)
        policy_names = policies_response['PolicyNames']
        
        inline_policies = {}
        for policy_name in policy_names:
            policy_response = iam.get_role_policy(
                RoleName=role_name,
                PolicyName=policy_name
            )
            inline_policies[policy_name] = policy_response['PolicyDocument']
        
        # Get attached managed policies
        attached_response = iam.list_attached_role_policies(RoleName=role_name)
        attached_policies = attached_response['AttachedPolicies']
        
        return {
            'role': role,
            'inline_policies': inline_policies,
            'attached_policies': attached_policies
        }
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return None
        raise

print("=" * 80)
print("IAM ROLES AUDIT - CURRENT AWS STATE")
print("=" * 80)

# Check Runtime Role
print("\n1. RUNTIME ROLE: agentcore-restaurant_booking-runtime-role")
print("-" * 80)
runtime_role = get_role_details('agentcore-restaurant_booking-runtime-role')

if runtime_role:
    print("✅ Role exists")
    print(f"\nAssumeRolePolicyDocument:")
    print(json.dumps(runtime_role['role']['AssumeRolePolicyDocument'], indent=2))
    
    print(f"\nInline Policies: {list(runtime_role['inline_policies'].keys())}")
    for policy_name, policy_doc in runtime_role['inline_policies'].items():
        print(f"\n--- Policy: {policy_name} ---")
        print(json.dumps(policy_doc, indent=2))
    
    print(f"\nAttached Managed Policies: {[p['PolicyName'] for p in runtime_role['attached_policies']]}")
else:
    print("❌ Role does not exist")

# Check Gateway Role
print("\n\n2. GATEWAY ROLE: agentcore-restaurant_booking-gateway-role")
print("-" * 80)
gateway_role = get_role_details('agentcore-restaurant_booking-gateway-role')

if gateway_role:
    print("✅ Role exists")
    print(f"\nAssumeRolePolicyDocument:")
    print(json.dumps(gateway_role['role']['AssumeRolePolicyDocument'], indent=2))
    
    print(f"\nInline Policies: {list(gateway_role['inline_policies'].keys())}")
    for policy_name, policy_doc in gateway_role['inline_policies'].items():
        print(f"\n--- Policy: {policy_name} ---")
        print(json.dumps(policy_doc, indent=2))
    
    print(f"\nAttached Managed Policies: {[p['PolicyName'] for p in gateway_role['attached_policies']]}")
else:
    print("❌ Role does not exist")

# Save to file for comparison
print("\n\n" + "=" * 80)
print("SAVING AUDIT RESULTS")
print("=" * 80)

audit_results = {
    'runtime_role': runtime_role,
    'gateway_role': gateway_role
}

with open('deployment/iam_roles_audit.json', 'w') as f:
    json.dump(audit_results, f, indent=2, default=str)

print("✅ Audit saved to: deployment/iam_roles_audit.json")
print("\nNext: Compare with utils/iam_roles.py to verify recreation script")
