# Quick Test Guide - Streamlit App

## ✅ Infrastructure Status
All components are already deployed:
- ✅ Memory ID: RestaurantBookingMemory-h16ClnB6f7
- ✅ Gateway URL: https://restaurant-booking-gateway-e7trb0r5cm...
- ✅ Runtime ARN: arn:aws:bedrock-agentcore:us-east-1:696072349808:runtime/restaurant_booking_orchestrator-A5ITpVHRPw

## 🚀 Start Streamlit App

```bash
cd /Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem/frontend-agentcore
streamlit run app.py
```

## 🧪 Test Scenarios

### Test 1: Search Restaurants (2 minutes)
1. **Enter User Info:**
   - User ID: `test_user_001`
   - Phone: `5551234567`

2. **Search Query:**
   ```
   Show me Italian restaurants in New York
   ```

3. **Expected Result:**
   - List of Italian restaurants
   - Restaurant names, ratings, locations
   - Check terminal for: `[DEBUG] Invoking Lambda: fetchRestaurantDetails-dev`

### Test 2: Make a Booking (3 minutes)
1. **After search, book:**
   ```
   Book a table for 2 at 7pm tomorrow at the first restaurant
   ```

2. **Provide details when asked:**
   - Name: `John Doe`
   - Phone: `5551234567` (already provided)
   - Date: `tomorrow` or `2024-01-16`
   - Time: `7pm` or `19:00`
   - Guests: `2`

3. **Expected Result:**
   - ✅ Booking Confirmed!
   - Booking ID displayed
   - Deposit amount shown
   - Check terminal for Lambda invocations:
     - `searchUserDetails`
     - `registerUser` (if new user)
     - `tokenAmountCalculation`
     - `bookATable`
     - `paymentAPI`

### Test 3: Multi-turn Conversation (5 minutes)
1. **Turn 1:** `I want to book a restaurant`
2. **Turn 2:** `Italian food in New York`
3. **Turn 3:** `Book the first one`
4. **Turn 4:** `For 4 people`
5. **Turn 5:** `Tomorrow at 8pm`
6. **Turn 6:** `My name is Jane Smith`

**Expected:** Agent remembers context across turns using AgentCore Memory

## 📊 What to Monitor

### Terminal Output
Look for these log messages:
```
[INFO] MCPToolClient initialized
[DEBUG] Invoking Lambda: <tool-name>
[DEBUG] Lambda response: {...}
```

### Streamlit Debug Mode
1. Enable in sidebar: `🐛 Debug Mode`
2. See session_id, user_id, metadata after each response

### CloudWatch Logs (Optional)
```bash
# View runtime logs
aws logs tail /aws/bedrock-agentcore/runtimes/restaurant_booking_orchestrator-A5ITpVHRPw --follow
```

## ✅ Success Criteria

- [ ] Streamlit app starts without errors
- [ ] Can search for restaurants
- [ ] Restaurant list displays correctly
- [ ] Can initiate booking
- [ ] Agent asks for missing information
- [ ] Booking completes successfully
- [ ] Confirmation message shows booking ID
- [ ] Terminal shows Lambda invocations
- [ ] No error messages in logs

## 🐛 Troubleshooting

### Issue: "GATEWAY_URL not set"
**Fix:** Already set in .env, restart Streamlit

### Issue: "Lambda invocation failed"
**Fix:** Check AWS credentials
```bash
aws sts get-caller-identity
```

### Issue: "Memory not found"
**Fix:** Memory ID is set, check if memory exists
```bash
aws bedrock-agentcore list-memories --region us-east-1
```

### Issue: Booking fails
**Check:**
1. DynamoDB tables exist (Restaurants, Users, Bookings, Payments)
2. Lambda functions are deployed
3. Lambda has DynamoDB permissions

## 📝 Test Results Template

```
Test Date: ___________
Tester: ___________

Test 1: Search Restaurants
- Status: [ ] Pass [ ] Fail
- Notes: _______________________

Test 2: Make Booking
- Status: [ ] Pass [ ] Fail
- Booking ID: _______________________
- Notes: _______________________

Test 3: Multi-turn Conversation
- Status: [ ] Pass [ ] Fail
- Notes: _______________________

Issues Found:
1. _______________________
2. _______________________

Overall Status: [ ] All Pass [ ] Some Failures
```

## 🎯 Next Steps After Testing

If all tests pass:
1. ✅ Mark Gateway integration as "Working with direct Lambda"
2. ✅ Document current architecture
3. ✅ Move to Phase 1: Weather Intelligence

If tests fail:
1. Check CloudWatch logs
2. Verify Lambda permissions
3. Test individual Lambda functions
4. Debug with test scripts in `tests/` folder
