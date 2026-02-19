#!/bin/bash
# Test mock weather service with curl

echo "============================================================"
echo "🌤️  MOCK WEATHER SERVICE - CURL TEST"
echo "============================================================"
echo ""
echo "Make sure service is running: python3 app.py"
echo ""

BASE_URL="http://localhost:8080"

echo "🔍 Test 1: Miami on 2026-02-10 at Morning"
echo "------------------------------------------------------------"
curl -s "${BASE_URL}/weather?city=Miami&date=2026-02-10&time_slot=Morning" | python3 -m json.tool
echo ""

echo "🔍 Test 2: New York on 2026-02-12 at Evening"
echo "------------------------------------------------------------"
curl -s "${BASE_URL}/weather?city=New%20York&date=2026-02-12&time_slot=Evening" | python3 -m json.tool
echo ""

echo "🔍 Test 3: San Francisco on 2026-02-15 at Afternoon"
echo "------------------------------------------------------------"
curl -s "${BASE_URL}/weather?city=San%20Francisco&date=2026-02-15&time_slot=Afternoon" | python3 -m json.tool
echo ""

echo "🔍 Test 4: Boston on 2026-02-14 at Night"
echo "------------------------------------------------------------"
curl -s "${BASE_URL}/weather?city=Boston&date=2026-02-14&time_slot=Night" | python3 -m json.tool
echo ""

echo "============================================================"
echo "✅ All curl tests completed!"
echo "============================================================"
