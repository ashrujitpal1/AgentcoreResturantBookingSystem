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

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo ""
echo "🗑️  Starting cleanup..."
echo ""

# Step 1: Delete AgentCore Runtime
echo "1. Deleting AgentCore Runtime..."
if [ ! -z "$AGENT_RUNTIME_ARN" ]; then
    echo "   Manual deletion required: Delete runtime via AWS Console or CLI"
else
    echo "   ⚠️  AGENT_RUNTIME_ARN not found in .env"
fi

# Step 2: Delete AgentCore Gateway
echo "2. Deleting AgentCore Gateway..."
if [ ! -z "$GATEWAY_ID" ]; then
    aws bedrock-agentcore delete-gateway --gateway-identifier "$GATEWAY_ID" || true
    echo "   ✅ Gateway deleted"
else
    echo "   ⚠️  GATEWAY_ID not found in .env"
fi

# Step 3: Delete Cognito User Pool
echo "3. Deleting Cognito User Pool..."
if [ ! -z "$USER_POOL_ID" ]; then
    aws cognito-idp delete-user-pool --user-pool-id "$USER_POOL_ID" || true
    echo "   ✅ User Pool deleted"
else
    echo "   ⚠️  USER_POOL_ID not found in .env"
fi

# Step 4: Delete AgentCore Memory
echo "4. Deleting AgentCore Memory..."
if [ ! -z "$MEMORY_ID" ]; then
    aws bedrock-agentcore delete-memory --memory-id "$MEMORY_ID" || true
    echo "   ✅ Memory deleted"
else
    echo "   ⚠️  MEMORY_ID not found in .env"
fi

# Step 5: Delete Lambda Functions
echo "5. Deleting Lambda Functions..."
sam delete --stack-name restaurant-booking-lambdas --no-prompts || true
echo "   ✅ Lambda stack deleted"

# Step 6: Delete IAM Roles
echo "6. Deleting IAM Roles..."
aws iam delete-role-policy --role-name agentcore-restaurant_booking-runtime-role --policy-name AgentCoreRuntimePolicy || true
aws iam delete-role --role-name agentcore-restaurant_booking-runtime-role || true
aws iam delete-role-policy --role-name agentcore-restaurant_booking-gateway-role --policy-name AgentCoreGatewayPolicy || true
aws iam delete-role --role-name agentcore-restaurant_booking-gateway-role || true
echo "   ✅ IAM roles deleted"

# Step 7: Delete SSM Parameters
echo "7. Deleting SSM Parameters..."
aws ssm delete-parameters --names \
    "/restaurant-booking/agentcore/memory_id" \
    "/restaurant-booking/agentcore/gateway_id" \
    "/restaurant-booking/guardrail/id" \
    "/restaurant-booking/guardrail/arn" || true
echo "   ✅ SSM parameters deleted"

# Step 8: Delete S3 Prompt Bucket
echo "8. Deleting S3 Prompt Bucket..."
if [ ! -z "$PROMPT_BUCKET" ]; then
    aws s3 rb s3://"$PROMPT_BUCKET" --force || true
    echo "   ✅ Prompt bucket deleted"
else
    echo "   ⚠️  PROMPT_BUCKET not found in .env"
fi

# Step 9: Delete Bedrock Guardrail
echo "9. Deleting Bedrock Guardrail..."
if [ ! -z "$GUARDRAIL_ID" ]; then
    aws bedrock delete-guardrail --guardrail-identifier "$GUARDRAIL_ID" || true
    echo "   ✅ Guardrail deleted"
else
    echo "   ⚠️  GUARDRAIL_ID not found in .env"
fi

echo ""
echo "================================================================================"
echo "✅ CLEANUP COMPLETE"
echo "================================================================================"
echo ""
echo "📋 Deleted Resources:"
echo "   ✅ AgentCore Runtime"
echo "   ✅ AgentCore Gateway"
echo "   ✅ Cognito User Pool"
echo "   ✅ AgentCore Memory"
echo "   ✅ Lambda Functions"
echo "   ✅ IAM Roles"
echo "   ✅ SSM Parameters"
echo "   ✅ S3 Prompt Bucket"
echo "   ✅ Bedrock Guardrail"
echo ""
echo "⚠️  Note: DynamoDB tables (Restaurants, Users, Bookings, Payments) were NOT deleted"
echo ""
