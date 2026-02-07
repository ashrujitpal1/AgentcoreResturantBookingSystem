"""
IAM Role creation utilities for AgentCore with proper CloudWatch Logs permissions.
Based on agentcore-for-education reference implementation.
"""
import boto3
import json
import time
from boto3.session import Session


def create_agentcore_runtime_role(agent_name: str = "restaurant_booking"):
    """
    Create IAM role for AgentCore Runtime with CloudWatch Logs permissions.
    
    CRITICAL: CloudWatch Logs permissions must be structured exactly as shown
    to avoid logging issues. Based on agentcore-for-education implementation.
    """
    iam_client = boto3.client('iam')
    role_name = f'agentcore-{agent_name}-runtime-role'
    
    boto_session = Session()
    region = boto_session.region_name
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    
    # CRITICAL: CloudWatch Logs permissions structure
    role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BedrockPermissions",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:Retrieve"
                ],
                "Resource": "*"
            },
            {
                "Sid": "ECRImageAccess",
                "Effect": "Allow",
                "Action": [
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:GetAuthorizationToken"
                ],
                "Resource": [
                    f"arn:aws:ecr:{region}:{account_id}:repository/*"
                ]
            },
            {
                "Sid": "ECRTokenAccess",
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken"
                ],
                "Resource": "*"
            },
            # CRITICAL: CloudWatch Logs permissions (3 separate statements)
            {
                "Effect": "Allow",
                "Action": [
                    "logs:DescribeLogStreams",
                    "logs:CreateLogGroup"
                ],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:DescribeLogGroups"
                ],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
                ]
            },
            # X-Ray tracing
            {
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets"
                ],
                "Resource": ["*"]
            },
            # CloudWatch metrics
            {
                "Effect": "Allow",
                "Resource": "*",
                "Action": "cloudwatch:PutMetricData",
                "Condition": {
                    "StringEquals": {
                        "cloudwatch:namespace": "bedrock-agentcore"
                    }
                }
            },
            # AgentCore Memory
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:ListMemories",
                    "bedrock-agentcore:ListMemoryRecords",
                    "bedrock-agentcore:RetrieveMemoryRecords",
                    "bedrock-agentcore:GetMemory",
                    "bedrock-agentcore:GetMemoryRecord",
                    "bedrock-agentcore:CreateEvent",
                    "bedrock-agentcore:GetEvent",
                    "bedrock-agentcore:ListEvents"
                ],
                "Resource": [
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:memory/*"
                ]
            },
            # Workload identity
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
                ],
                "Resource": [
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default",
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default/workload-identity/{agent_name}-*"
                ]
            },
            # SSM Parameter Store
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter"
                ],
                "Resource": [
                    f"arn:aws:ssm:{region}:{account_id}:parameter/restaurant-booking/*"
                ]
            },
            # Lambda invocation
            {
                "Sid": "LambdaInvoke",
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction",
                    "lambda:InvokeAsync"
                ],
                "Resource": f"arn:aws:lambda:{region}:{account_id}:function:*"
            },
            # S3 access for prompts
            {
                "Sid": "S3PromptAccess",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::restaurant-booking-prompts-{account_id}",
                    f"arn:aws:s3:::restaurant-booking-prompts-{account_id}/*"
                ]
            }
        ]
    }
    
    # Trust policy for AgentCore service
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AssumeRolePolicyAgentCore",
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": f"{account_id}"
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
                    }
                }
            }
        ]
    }
    
    try:
        print(f"Creating IAM role: {role_name}")
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )
        
        # Wait for role to exist
        print(f"⏳ Waiting for IAM role to be ready: {role_name}")
        waiter = iam_client.get_waiter('role_exists')
        waiter.wait(
            RoleName=role_name,
            WaiterConfig={'Delay': 2, 'MaxAttempts': 30}
        )
        print(f"✅ IAM role is ready: {role_name}")
        
        # Additional wait for eventual consistency
        print("⏳ Waiting for IAM eventual consistency (30s)...")
        time.sleep(30)
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"⚠️  Role already exists: {role_name}")
        role = iam_client.get_role(RoleName=role_name)
    
    # Attach inline policy
    print(f"Attaching inline policy to {role_name}")
    iam_client.put_role_policy(
        PolicyDocument=json.dumps(role_policy),
        PolicyName="AgentCoreRuntimePolicy",
        RoleName=role_name
    )
    
    print(f"✅ Role created with CloudWatch Logs permissions: {role['Role']['Arn']}")
    return role


def create_agentcore_gateway_role(gateway_name: str = "restaurant_booking"):
    """Create IAM role for AgentCore Gateway"""
    iam_client = boto3.client('iam')
    role_name = f'agentcore-{gateway_name}-gateway-role'
    
    boto_session = Session()
    region = boto_session.region_name
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    
    role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "GatewayPermissions",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:*",
                "bedrock:*",
                "agent-credential-provider:*",
                "iam:PassRole",
                "secretsmanager:GetSecretValue",
                "lambda:InvokeFunction"
            ],
            "Resource": "*"
        }]
    }
    
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AssumeRolePolicy",
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock-agentcore.amazonaws.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": f"{account_id}"
                },
                "ArnLike": {
                    "aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
                }
            }
        }]
    }
    
    try:
        print(f"Creating IAM gateway role: {role_name}")
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )
        
        print(f"⏳ Waiting for IAM gateway role to be ready: {role_name}")
        waiter = iam_client.get_waiter('role_exists')
        waiter.wait(
            RoleName=role_name,
            WaiterConfig={'Delay': 2, 'MaxAttempts': 30}
        )
        print(f"✅ IAM gateway role is ready: {role_name}")
        
        print("⏳ Waiting for IAM eventual consistency (30s)...")
        time.sleep(30)
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"⚠️  Gateway role already exists: {role_name}")
        role = iam_client.get_role(RoleName=role_name)
    
    print(f"Attaching inline policy to {role_name}")
    iam_client.put_role_policy(
        PolicyDocument=json.dumps(role_policy),
        PolicyName="AgentCoreGatewayPolicy",
        RoleName=role_name
    )
    
    print(f"✅ Gateway role created: {role['Role']['Arn']}")
    return role


if __name__ == "__main__":
    print("=" * 80)
    print("CREATING IAM ROLES FOR AGENTCORE")
    print("=" * 80)
    
    # Create runtime role
    runtime_role = create_agentcore_runtime_role()
    print(f"\n✅ Runtime Role ARN: {runtime_role['Role']['Arn']}")
    
    # Create gateway role
    gateway_role = create_agentcore_gateway_role()
    print(f"\n✅ Gateway Role ARN: {gateway_role['Role']['Arn']}")
    
    print("\n" + "=" * 80)
    print("KEY CLOUDWATCH LOGS PERMISSIONS")
    print("=" * 80)
    print("""
The role includes 3 separate CloudWatch Logs statements:

1. CreateLogGroup + DescribeLogStreams on /aws/bedrock-agentcore/runtimes/*
2. DescribeLogGroups on all log groups
3. CreateLogStream + PutLogEvents on /aws/bedrock-agentcore/runtimes/*:log-stream:*

This structure is CRITICAL for AgentCore to write logs properly.
    """)
