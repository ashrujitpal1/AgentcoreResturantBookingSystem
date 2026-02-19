#!/bin/bash
# Step-by-step Cognito setup for Weather API

USER_POOL_ID="us-east-1_v7ilQRXCR"
REGION="us-east-1"

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║         Cognito Setup for Weather API - Step-by-Step Guide                ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check if custom attribute exists
echo "📋 Step 1: Checking for custom:tier attribute..."
echo "────────────────────────────────────────────────────────────────────────────"

ATTR_CHECK=$(aws cognito-idp describe-user-pool \
  --user-pool-id $USER_POOL_ID \
  --region $REGION \
  --query 'UserPool.SchemaAttributes[?Name==`custom:tier`]' \
  --output json 2>/dev/null)

if [ "$ATTR_CHECK" == "[]" ] || [ -z "$ATTR_CHECK" ]; then
    echo "⚠️  Custom attribute 'tier' NOT found"
    echo ""
    echo "📝 MANUAL ACTION REQUIRED:"
    echo "────────────────────────────────────────────────────────────────────────────"
    echo ""
    echo "Please add the custom attribute via AWS Console:"
    echo ""
    echo "1. Open: https://console.aws.amazon.com/cognito/v2/idp/user-pools"
    echo ""
    echo "2. Select User Pool: $USER_POOL_ID"
    echo ""
    echo "3. Navigate to: Sign-up experience → Custom attributes"
    echo ""
    echo "4. Click: 'Add custom attribute'"
    echo ""
    echo "5. Configure:"
    echo "   • Attribute name: tier"
    echo "   • Attribute data type: String"
    echo "   • Minimum length: 4"
    echo "   • Maximum length: 10"
    echo "   • Mutable: ✓ (checked)"
    echo ""
    echo "6. Click: 'Save changes'"
    echo ""
    echo "────────────────────────────────────────────────────────────────────────────"
    echo ""
    read -p "Press ENTER after you've added the custom attribute..."
    echo ""
    
    # Re-check
    ATTR_CHECK=$(aws cognito-idp describe-user-pool \
      --user-pool-id $USER_POOL_ID \
      --region $REGION \
      --query 'UserPool.SchemaAttributes[?Name==`custom:tier`]' \
      --output json 2>/dev/null)
    
    if [ "$ATTR_CHECK" == "[]" ] || [ -z "$ATTR_CHECK" ]; then
        echo "❌ Custom attribute still not found. Please verify and try again."
        exit 1
    fi
fi

echo "✅ Custom attribute 'tier' exists!"
echo ""

# Step 2: Run Python script to create users
echo "📋 Step 2: Creating test users..."
echo "────────────────────────────────────────────────────────────────────────────"
echo ""

python3 deploy-scripts/update_cognito_for_weather.py $USER_POOL_ID $REGION

if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ COGNITO SETUP COMPLETE!                              ║"
    echo "╚════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📊 What was configured:"
    echo "   ✓ Custom attribute 'tier' verified"
    echo "   ✓ Test user 'normal_user' created (tier: normal)"
    echo "   ✓ Test user 'gold_user' created (tier: gold)"
    echo "   ✓ Users verified and tested"
    echo ""
    echo "🔑 Test Credentials:"
    echo "   • normal_user / WeatherTest123!"
    echo "   • gold_user / WeatherTest123!"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. cd mock-weather-service"
    echo "   2. Implement auth.py (JWT verification)"
    echo "   3. Implement middleware.py (authorization decorator)"
    echo "   4. Update app.py with @require_auth decorators"
    echo ""
else
    echo ""
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi
