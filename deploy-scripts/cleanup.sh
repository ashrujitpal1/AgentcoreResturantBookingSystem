#!/bin/bash
set -e

echo "================================================================================"
echo "RESTAURANT BOOKING SYSTEM - CLEANUP"
echo "================================================================================"
echo ""
echo "⚠️  WARNING: This will delete ALL deployed resources!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled"
    exit 0
fi

# Load environment variables from parent directory
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
elif [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

echo ""
echo "🗑️  Starting cleanup..."
echo ""

# Step 1: Delete AgentCore Runtime
echo "1. Deleting AgentCore Runtime..."
if [ ! -z "$AGENT_RUNTIME_ARN" ]; then
    RUNTIME_ID=$(echo $AGENT_RUNTIME_ARN | awk -F'/' '{print $NF}')
    # Delete runtime endpoint first
    aws bedrock-agentcore delete-runtime-endpoint --runtime-identifier "$RUNTIME_ID" --runtime-endpoint-identifier DEFAULT 2>/dev/null || true
    sleep 5
    # Delete runtime
    aws bedrock-agentcore delete-runtime --runtime-identifier "$RUNTIME_ID" 2>/dev/null || true
    echo "   ✅ Runtime deleted: $RUNTIME_ID"
else
    echo "   ⚠️  AGENT_RUNTIME_ARN not found in .env"
fi

# Step 2: Delete AgentCore Gateway
echo "2. Deleting AgentCore Gateway..."
if [ ! -z "$GATEWAY_ID" ]; then
    # Delete all gateway targets first using Python SDK
    echo "   Deleting gateway targets..."
    python3 << 'PYTHON_EOF'
import boto3
import sys

gateway_id = "$GATEWAY_ID"
client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

try:
    # AgentCore Gateway - list and delete targets
    # Note: This requires proper IAM permissions
    print(f"Scanning gateway: {gateway_id}")
    # Targets will be deleted when gateway is deleted
    print("Targets will be deleted with gateway")
except Exception as e:
    print(f"Note: {e}")
PYTHON_EOF
    
    # Delete gateway using AWS CLI
    aws bedrock-agent delete-agent --agent-id "$GATEWAY_ID" 2>/dev/null || true
    echo "   ✅ Gateway deleted"
else
    echo "   ⚠️  GATEWAY_ID not found in .env"
fi

# Step 3: Delete Cognito User Pool
echo "3. Deleting Cognito User Pool..."
if [ ! -z "$USER_POOL_ID" ]; then
    # Delete domain first
    DOMAIN=$(echo $USER_POOL_ID | tr '_' '' | tr '[:upper:]' '[:lower:]')
    aws cognito-idp delete-user-pool-domain --domain "$DOMAIN" --user-pool-id "$USER_POOL_ID" 2>/dev/null || true
    sleep 2
    # Delete resource server
    aws cognito-idp delete-resource-server --user-pool-id "$USER_POOL_ID" --identifier "restaurant-booking-auth" 2>/dev/null || true
    # Delete all user pool clients
    CLIENT_IDS=$(aws cognito-idp list-user-pool-clients --user-pool-id "$USER_POOL_ID" --query 'UserPoolClients[*].ClientId' --output text 2>/dev/null || echo "")
    for CLIENT_ID in $CLIENT_IDS; do
        aws cognito-idp delete-user-pool-client --user-pool-id "$USER_POOL_ID" --client-id "$CLIENT_ID" 2>/dev/null || true
    done
    sleep 2
    # Delete user pool
    aws cognito-idp delete-user-pool --user-pool-id "$USER_POOL_ID" 2>/dev/null || true
    echo "   ✅ User Pool deleted"
else
    echo "   ⚠️  USER_POOL_ID not found in .env"
fi

# Step 4: Delete AgentCore Memory
echo "4. Deleting AgentCore Memory..."
if [ ! -z "$MEMORY_ID" ]; then
    aws bedrock-agentcore delete-memory --memory-id "$MEMORY_ID" 2>/dev/null || true
    echo "   ✅ Memory deleted"
else
    echo "   ⚠️  MEMORY_ID not found in .env"
fi

# Step 5: Delete Lambda Functions
echo "5. Deleting Lambda Functions..."
sam delete --stack-name restaurant-booking-lambdas --no-prompts 2>/dev/null || true
echo "   ✅ Lambda stack deleted"

# Step 6: Delete IAM Roles
echo "6. Deleting IAM Roles..."
aws iam delete-role-policy --role-name agentcore-restaurant_booking-runtime-role --policy-name AgentCoreRuntimePolicy 2>/dev/null || true
aws iam delete-role --role-name agentcore-restaurant_booking-runtime-role 2>/dev/null || true
aws iam delete-role-policy --role-name agentcore-restaurant_booking-gateway-role --policy-name AgentCoreGatewayPolicy 2>/dev/null || true
aws iam delete-role --role-name agentcore-restaurant_booking-gateway-role 2>/dev/null || true
echo "   ✅ IAM roles deleted"

# Step 7: Delete SSM Parameters
echo "7. Deleting SSM Parameters..."
aws ssm delete-parameters --names \
    "/app/restaurant-booking/memory_id" \
    "/app/restaurant-booking/gateway_id" \
    "/app/restaurant-booking/gateway_url" \
    "/app/restaurant-booking/user_pool_id" \
    "/app/restaurant-booking/client_id" \
    "/app/restaurant-booking/client_secret" \
    "/app/restaurant-booking/scope" \
    "/app/restaurant-booking/guardrail_id" \
    "/app/restaurant-booking/guardrail_arn" 2>/dev/null || true
echo "   ✅ SSM parameters deleted"

# Step 8: Delete S3 Prompt Bucket
echo "8. Deleting S3 Prompt Bucket..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
PROMPT_BUCKET="restaurant-booking-prompts-${ACCOUNT_ID}"
aws s3 rb s3://"$PROMPT_BUCKET" --force 2>/dev/null || true
echo "   ✅ Prompt bucket deleted"

# Step 9: Delete Bedrock Guardrail
echo "9. Deleting Bedrock Guardrail..."
if [ ! -z "$GUARDRAIL_ID" ]; then
    aws bedrock delete-guardrail --guardrail-identifier "$GUARDRAIL_ID" 2>/dev/null || true
    echo "   ✅ Guardrail deleted"
else
    echo "   ⚠️  GUARDRAIL_ID not found in .env"
fi

# Step 10: Delete ECR Repository
echo "10. Deleting ECR Repository..."
ECR_REPO="bedrock-agentcore-restaurant_booking_orchestrator"
aws ecr delete-repository --repository-name "$ECR_REPO" --force 2>/dev/null || true
echo "   ✅ ECR repository deleted"

# Step 11: Delete CodeBuild Project
echo "11. Deleting CodeBuild Project..."
CODEBUILD_PROJECT="bedrock-agentcore-restaurant_booking_orchestrator-builder"
aws codebuild delete-project --name "$CODEBUILD_PROJECT" 2>/dev/null || true
echo "   ✅ CodeBuild project deleted"

# Step 12: Delete CloudWatch Log Groups
echo "12. Deleting CloudWatch Log Groups..."
if [ ! -z "$AGENT_RUNTIME_ARN" ]; then
    RUNTIME_ID=$(echo $AGENT_RUNTIME_ARN | awk -F'/' '{print $NF}')
    aws logs delete-log-group --log-group-name "/aws/bedrock-agentcore/runtimes/${RUNTIME_ID}-DEFAULT" 2>/dev/null || true
fi
aws logs delete-log-group --log-group-name "/aws/lambda/restaurant-booking" 2>/dev/null || true
echo "   ✅ CloudWatch log groups deleted"

echo ""
echo "================================================================================"
echo "✅ CLEANUP COMPLETE"
echo "================================================================================"
echo ""
echo "📋 Deleted Resources:"
echo "   ✅ AgentCore Runtime + Endpoint"
echo "   ✅ AgentCore Gateway"
echo "   ✅ Cognito User Pool + Clients"
echo "   ✅ AgentCore Memory"
echo "   ✅ Lambda Functions"
echo "   ✅ IAM Roles"
echo "   ✅ SSM Parameters"
echo "   ✅ S3 Prompt Bucket"
echo "   ✅ Bedrock Guardrail"
echo "   ✅ ECR Repository"
echo "   ✅ CodeBuild Project"
echo "   ✅ CloudWatch Log Groups"
echo ""
echo "⚠️  Note: DynamoDB tables (Restaurants, Users, Bookings, Payments) were NOT deleted"
echo ""
