# AgentCore Memory-Based Incremental Booking - COMPLETE

## ✅ Implementation Complete

The system now uses **AgentCore Memory** to persist booking parameters across conversation turns.

### How It Works

1. **Storage**: After each turn, booking params are stored in AgentCore Memory metadata (base64 encoded)
2. **Retrieval**: At the start of each turn, the latest params are retrieved from memory using `list_events`
3. **Accumulation**: New params from current turn are merged with retrieved params
4. **Validation**: Missing fields are detected and user is prompted

### Key Components

#### Memory Storage (`_store_memory`)
```python
# Encode params as base64 to comply with AgentCore Memory validation
params_b64 = base64.b64encode(json.dumps(params).encode()).decode()
memory_metadata = {'booking_params_b64': {'stringValue': params_b64}}

memory_client.create_event(
    memoryId=memory_id,
    actorId=user_id,
    sessionId=session_id,
    metadata=memory_metadata
)
```

#### Memory Retrieval (`_retrieve_memory`)
```python
# Use list_events with sessionId to get session-specific events
response = memory_client.list_events(
    memoryId=memory_id,
    actorId=user_id,
    sessionId=session_id
)

# Get most recent params (iterate in reverse)
for event in reversed(events):
    if 'booking_params_b64' in event['metadata']:
        params_b64 = event['metadata']['booking_params_b64']['stringValue']
        booking_params = json.loads(base64.b64decode(params_b64))
        break
```

#### Parameter Accumulation (`booking_agent.py`)
```python
# Start with params from memory/context
params = context.get("partial_params", {}).copy()

# Extract new params from user message
new_params = extract_from_llm(user_message)

# Merge (only update non-null values)
for key, value in new_params.items():
    if value:
        params[key] = value
```

### AgentCore Memory Constraints

**CRITICAL**: AgentCore Memory metadata has strict validation:
- Pattern: `[a-zA-Z0-9\s._:/=+@-]*` (no special chars like `{}[]"`)
- Max length: 256 characters per value

**Solution**: Use base64 encoding for JSON data

### Testing

```bash
# Test with Streamlit (maintains session state)
cd frontend
streamlit run app.py

# Test with delays (allows memory indexing)
python3 tests/test_memory_delay.py
```

### Example Flow

**Turn 1**: "Book Curry Leaf"
- Extracts: `{restaurantName: "Curry Leaf"}`
- Stores to memory
- Asks for: name, phone, date, time, guests

**Turn 2**: "John Smith, phone 5551234567"
- Retrieves from memory: `{restaurantName: "Curry Leaf"}`
- Extracts: `{userName: "John Smith", userMobileNo: "5551234567"}`
- Merges: `{restaurantName, userName, userMobileNo}`
- Stores to memory
- Asks for: date, time, guests

**Turn 3**: "4 people on 2026-03-15 at 19:00"
- Retrieves from memory: `{restaurantName, userName, userMobileNo}`
- Extracts: `{noOfGuests: 4, date: "2026-03-15", time: "19:00"}`
- Merges: ALL fields present ✅
- Executes booking

### Current Status

✅ Memory storage with base64 encoding  
✅ Memory retrieval using list_events  
✅ Parameter extraction and merging  
✅ Missing field detection  
✅ Works with Streamlit (session persistence)  

⚠️ Direct workflow tests need same session_id across turns  
⚠️ Memory indexing may have slight delay (use same session)

### Usage

**Streamlit App** (Recommended):
```bash
cd frontend
streamlit run app.py
```
- Enter User ID and Phone
- Have multi-turn conversation
- Params accumulate automatically via memory

**Direct API**:
```python
workflow = RestaurantBookingWorkflow(mcp_tools)
user_id = "john_123"
session_id = "session_" + "x" * 17  # Min 33 chars

# Turn 1
r1 = workflow.invoke("Book Curry Leaf", user_id, session_id)

# Turn 2 (same session_id!)
r2 = workflow.invoke("John Smith, 5551234567", user_id, session_id)

# Turn 3 (same session_id!)
r3 = workflow.invoke("4 people on 2026-03-15 at 19:00", user_id, session_id)
```

### Files Modified

1. `src/workflows/restaurant_workflow.py`
   - `_store_memory`: Base64 encode params
   - `_retrieve_memory`: Use list_events, decode base64
   - `invoke`: Initialize state with memory params

2. `src/agents/booking_agent.py`
   - `_extract_booking_params`: Merge with partial_params from context
   - `_check_missing_fields`: Detect missing required fields
   - `_format_missing_fields_prompt`: User-friendly prompts

3. `src/workflows/state.py`
   - Added `partial_booking_params` field

4. `frontend/app.py`
   - Added phone number input
   - Auto-injects phone into booking requests

## Summary

**AgentCore Memory successfully stores and retrieves booking state across conversation turns**, enabling true incremental information gathering. The system works end-to-end with proper session management.
