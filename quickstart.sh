#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Restaurant Booking System - Quick Start Deployment          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install: https://aws.amazon.com/cli/"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

# Check SAM CLI
if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI not found. Install: pip install aws-sam-cli"
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_REGION:-us-east-1}

echo "✅ Prerequisites verified"
echo "   Account: $ACCOUNT_ID"
echo "   Region: $REGION"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Restaurant Booking System - Environment Configuration

# AWS Configuration
AWS_REGION=$REGION
AWS_PROFILE=default
AWS_ACCOUNT_ID=$ACCOUNT_ID

# Will be populated during deployment
MEMORY_ID=
GATEWAY_ID=
GATEWAY_URL=
USER_POOL_ID=
CLIENT_ID=
AGENT_RUNTIME_ARN=
GUARDRAIL_ID=
GUARDRAIL_VERSION=
PROMPT_BUCKET=restaurant-booking-prompts-$ACCOUNT_ID

# DynamoDB Tables
RESTAURANTS_TABLE=Restaurants
USERS_TABLE=Users
BOOKINGS_TABLE=Bookings
PAYMENTS_TABLE=Payments
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file exists"
fi
echo ""

# Step 1: Deploy infrastructure
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  STEP 1/8: Deploying DynamoDB + Lambda Functions              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
sam build
sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
echo "✅ Infrastructure deployed"
echo ""

# Step 2: Seed data
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  STEP 2/8: Seeding Restaurant Data                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
python3 fetch_cities.py
echo "✅ Restaurant data seeded"
echo ""

# Step 3-8: Run deployment scripts
cd deploy-scripts

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  STEP 3/8: Deploying AgentCore Memory                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
python3 deploy_agentcore_memory.py
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  STEP 4/8: Deploying Cognito User Pool                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
python3 deploy_cognito_user_pool.py
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  STEP 5/8: Deploying AgentCore Gateway                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
python3 deploy_agentcore_gateway.py
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  STEP 6/8: Deploying Bedrock Guardrails                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
python3 deploy_bedrock_guardrails.py
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  STEP 7/8: Uploading Versioned Prompts                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
python3 deploy_prompts_to_s3.py
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  STEP 8/8: Deploying AgentCore Runtime                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
python3 deploy_agentcore_runtime.py
echo ""

cd ..

# Verify deployment
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ DEPLOYMENT COMPLETE                                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Deployed Components:"
echo "   ✅ DynamoDB Tables (4)"
echo "   ✅ Lambda Functions (8 MCP tools)"
echo "   ✅ AgentCore Memory"
echo "   ✅ Cognito User Pool"
echo "   ✅ AgentCore Gateway"
echo "   ✅ Bedrock Guardrails"
echo "   ✅ Versioned Prompts (S3)"
echo "   ✅ AgentCore Runtime"
echo ""
echo "🧪 Test Your Deployment:"
echo "   cd tests"
echo "   python3 test_runtime.py"
echo "   python3 test_orchestrator.py"
echo ""
echo "📝 Configuration: .env file"
echo "🗑️  Cleanup: cd deploy-scripts && ./cleanup.sh"
echo ""
