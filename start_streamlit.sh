#!/bin/bash
# Quick test script for Streamlit app

echo "🚀 Starting Streamlit App..."
echo ""
echo "📋 Test Instructions:"
echo "1. Enter User ID: test_user_001"
echo "2. Enter Phone: 5551234567"
echo "3. Try: 'Show me Italian restaurants in New York'"
echo "4. Then: 'Book a table for 2 at 7pm tomorrow'"
echo ""
echo "✅ Runtime deployed: restaurant_booking_orchestrator-A5ITpVHRPw"
echo "✅ Memory enabled: RestaurantBookingMemory-h16ClnB6f7"
echo ""

cd /Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem/frontend-agentcore
streamlit run app.py
