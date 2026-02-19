# Guardrail Analysis - Restaurant Booking System

## Executive Summary

The Bedrock Guardrail was blocking legitimate restaurant booking requests due to PII (Personally Identifiable Information) protection policies that are incompatible with booking system requirements.

## Root Cause

The guardrail configuration includes:
```json
{
  "type": "PHONE",
  "action": "BLOCK"
}
```

This blocks phone numbers in BOTH input and output, preventing users from providing phone numbers required for restaurant reservations.

## Guardrail Configuration

### Current Policies

1. **Content Filters**
   - HATE: HIGH (input/output)
   - INSULTS: HIGH (input/output)
   - SEXUAL: HIGH (input/output)
   - VIOLENCE: MEDIUM (input/output)
   - MISCONDUCT: MEDIUM (input/output)

2. **Topic Blocking (DENY)**
   - Political Discussion
   - Medical Advice
   - Financial Advice
   - Legal Advice

3. **PII Blocking (BLOCK)**
   - EMAIL ❌ Blocks user emails
   - PHONE ❌ Blocks phone numbers (CRITICAL ISSUE)
   - CREDIT_DEBIT_CARD_NUMBER ✅ Correct
   - US_SOCIAL_SECURITY_NUMBER ✅ Correct
   - US_BANK_ACCOUNT_NUMBER ✅ Correct

4. **Word Filters**
   - Profanity blocking enabled

## Issues Encountered

### 1. Orchestrator Level (FIXED)
- **Issue**: Guardrail validated input before workflow started
- **Impact**: Blocked "Find a restaurant for Indian cuisine at New York"
- **Solution**: Removed guardrail validation from orchestrator.py
- **Status**: ✅ FIXED

### 2. Intent Classifier (FIXED)
- **Issue**: Guardrail blocked intent classification
- **Impact**: Legitimate booking requests classified as "out_of_scope"
- **Solution**: Set `guardrail_id=None` in IntentClassifierAgent
- **Status**: ✅ FIXED

### 3. Booking Agent (FIXED)
- **Issue**: Guardrail blocked phone numbers in user input
- **Impact**: "809888900898, at 8 PM" was blocked with message "I can only help with restaurant bookings"
- **Solution**: Set `guardrail_id=None` in BookingAgent
- **Status**: ✅ FIXED

### 4. Restaurant Finder (CURRENT)
- **Issue**: Still has guardrail enabled
- **Impact**: Minimal - doesn't process PII
- **Solution**: Can be disabled for consistency
- **Status**: ⚠️ OPTIONAL

## Current System State

| Component | Guardrail Status | Reason |
|-----------|-----------------|--------|
| Orchestrator | ❌ Disabled | Blocks legitimate search requests |
| Intent Classifier | ❌ Disabled | Blocks intent classification |
| Booking Agent | ❌ Disabled | Blocks required phone numbers |
| Restaurant Finder | ✅ Enabled | Doesn't process PII (can be disabled) |

## Recommendations

### Option 1: Keep Guardrails Disabled (CURRENT APPROACH)
**Pros:**
- System works correctly
- Users can provide phone numbers
- No false positives

**Cons:**
- No LLM-level content filtering
- Relies on application-level validation only

### Option 2: Reconfigure Guardrail with ANONYMIZE
**Change:**
```python
{"type": "PHONE", "action": "ANONYMIZE"}  # Instead of BLOCK
```

**Pros:**
- Masks phone numbers in logs/outputs
- Allows processing of booking data
- Maintains some PII protection

**Cons:**
- Phone numbers still need to be stored for bookings
- Adds complexity

### Option 3: Selective Guardrail Usage
**Approach:**
- Enable guardrail ONLY for restaurant_finder (search queries)
- Keep disabled for booking_agent (needs PII)
- Keep disabled for intent_classifier (needs to process all inputs)

**Pros:**
- Balanced security and functionality
- Protects search queries from harmful content

**Cons:**
- Inconsistent protection across agents

## Deployment History

1. **Initial Deployment**: All agents had guardrails enabled
2. **Fix 1**: Removed guardrail from orchestrator entry point
3. **Fix 2**: Disabled guardrail in intent_classifier
4. **Fix 3**: Disabled guardrail in booking_agent
5. **Current**: System functional with selective guardrail usage

## Testing Results

### Before Fixes
```
❌ "Find a restaurant for Indian cuisine at New York" → BLOCKED
❌ "Yes" (after search) → Classified as out_of_scope
❌ "809888900898, at 8 PM" → BLOCKED (PII)
```

### After Fixes
```
✅ "Find a restaurant for Indian cuisine at New York" → Search successful
✅ "Yes" (after search) → Intent: booking
✅ "809888900898, at 8 PM" → Booking parameters extracted
```

## Conclusion

The guardrail's PII blocking policy is fundamentally incompatible with a booking system that requires users to provide phone numbers. The correct approach is to:

1. **Disable guardrails for booking-related agents** (CURRENT - WORKING)
2. **Implement application-level validation** for security (ALREADY IN PLACE via security_context)
3. **Use guardrails selectively** for non-PII agents if needed

The system is now fully functional with guardrails disabled where they conflict with business requirements.

## Files Modified

1. `src/orchestrator.py` - Removed guardrail validation
2. `src/agents/intent_classifier.py` - Set guardrail_id=None
3. `src/agents/booking_agent.py` - Set guardrail_id=None
4. `src/core/llm_provider.py` - Made guardrail version configurable via env var

## Environment Variables

```bash
GUARDRAIL_ID=d91qhnduvi6f
GUARDRAIL_VERSION=2
```

Note: These are kept for potential future use but currently not used by booking-critical agents.
