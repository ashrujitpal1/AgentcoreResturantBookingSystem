#!/bin/bash
set -e  # Exit on error

echo "================================================================================"
echo "RESTAURANT BOOKING SYSTEM - COMPLETE DEPLOYMENT"
echo "================================================================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

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

# Step 4: Deploy AgentCore Gateway
echo "================================================================================"
echo "STEP 4: Deploying AgentCore Gateway"
echo "================================================================================"
python3 deploy_agentcore_gateway.py
echo "✅ AgentCore Gateway deployed"
echo ""

# Step 5: Deploy Bedrock Guardrails
echo "================================================================================"
echo "STEP 5: Deploying Bedrock Guardrails"
echo "================================================================================"
python3 deploy_bedrock_guardrails.py
echo "✅ Bedrock Guardrails deployed"
echo ""

# Step 6: Upload Prompts to S3
echo "================================================================================"
echo "STEP 6: Uploading Versioned Prompts to S3"
echo "================================================================================"
python3 deploy_prompts_to_s3.py
echo "✅ Prompts uploaded to S3"
echo ""

# Step 7: Deploy AgentCore Runtime (Strands + LangGraph)
echo "================================================================================"
echo "STEP 7: Deploying AgentCore Runtime (Strands + LangGraph)"
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
