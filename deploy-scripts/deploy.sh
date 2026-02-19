#!/bin/bash
set -e  # Exit on error

echo "================================================================================"
echo "RESTAURANT BOOKING SYSTEM - COMPLETE DEPLOYMENT"
echo "================================================================================"
echo ""

# Load environment variables from parent directory
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
elif [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

echo "📋 Deployment Configuration:"
echo "   AWS Region: ${AWS_REGION:-us-east-1}"
echo "   AWS Profile: ${AWS_PROFILE:-default}"
echo ""

# Step 1: Deploy Lambda Functions (MCP Tools)
echo "================================================================================"
echo "STEP 1: Deploying Lambda Functions (MCP Tools)"
echo "================================================================================"
echo "⏭️  Skipping Lambda deployment (already deployed via SAM)"
echo ""

# Step 2: Deploy AgentCore Memory
echo "================================================================================"
echo "STEP 2: Deploying AgentCore Memory"
echo "================================================================================"
python3 deploy_agentcore_memory.py
echo "✅ AgentCore Memory deployed"
echo ""

# Step 3: Deploy Cognito User Pool (for Gateway OAuth2)
echo "================================================================================"
echo "STEP 3: Deploying Cognito User Pool"
echo "================================================================================"
python3 deploy_cognito_user_pool.py
echo "✅ Cognito User Pool deployed"
echo ""

# Step 4: Configure Cognito for Weather API
echo "================================================================================"
echo "STEP 4: Configuring Cognito for Weather API (RBAC)"
echo "================================================================================"
# Read USER_POOL_ID from .env (updated in Step 3)
if [ -f ../.env ]; then
    export $(cat ../.env | grep '^USER_POOL_ID=' | xargs)
elif [ -f .env ]; then
    export $(cat .env | grep '^USER_POOL_ID=' | xargs)
fi
python3 update_cognito_for_weather.py "${USER_POOL_ID}" "${AWS_REGION}"
echo "✅ Weather API Cognito configured"
echo ""

# Step 5: Deploy AgentCore Gateway
echo "================================================================================"
echo "STEP 5: Deploying AgentCore Gateway"
echo "================================================================================"
python3 deploy_agentcore_gateway.py
echo "✅ AgentCore Gateway deployed"
echo ""

# Step 5: Deploy Bedrock Guardrails
echo "================================================================================"
echo "STEP 6: Deploying Bedrock Guardrails"
echo "================================================================================"
python3 deploy_bedrock_guardrails.py
echo "✅ Bedrock Guardrails deployed"
echo ""

# Step 6: Upload Prompts to S3
echo "================================================================================"
echo "STEP 7: Uploading Versioned Prompts to S3"
echo "================================================================================"
python3 deploy_prompts_to_s3.py
echo "✅ Prompts uploaded to S3"
echo ""

# Step 7: Deploy AgentCore Runtime (Strands + LangGraph)
echo "================================================================================"
echo "STEP 8: Deploying AgentCore Runtime (Strands + LangGraph)"
echo "================================================================================"
python3 deploy_agentcore_runtime.py
echo "✅ AgentCore Runtime deployed"
echo ""

echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE"
echo "================================================================================"
echo ""
echo "📋 Deployment Summary:"
echo "   ✅ Lambda Functions (MCP Tools)"
echo "   ✅ AgentCore Memory"
echo "   ✅ Cognito User Pool"
echo "   ✅ Weather API Cognito (RBAC)"
echo "   ✅ AgentCore Gateway"
echo "   ✅ Bedrock Guardrails"
echo "   ✅ Versioned Prompts (S3)"
echo "   ✅ AgentCore Runtime (Strands + LangGraph)"
echo ""
echo "🧪 Next Steps:"
echo "   1. Test locally: python3 tests/test_orchestrator.py"
echo "   2. Check CloudWatch Logs: /aws/bedrock-agentcore/runtimes/<runtime-id>"
echo "   3. Invoke agent: aws bedrock-agentcore-runtime invoke-agent"
echo ""
echo "📝 Configuration stored in:"
echo "   - .env file (updated with ARNs and IDs)"
echo "   - SSM Parameter Store (/restaurant-booking/*)"
echo ""
