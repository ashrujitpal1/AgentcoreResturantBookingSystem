# Incremental Booking Feature

## How It Works

The booking agent now supports **incremental information gathering** across multiple conversation turns.

### Features

1. **Missing Field Detection**: Automatically detects which required fields are missing
2. **Context Accumulation**: Remembers information provided in previous turns
3. **Memory Integration**: Retrieves conversation history from AgentCore Memory
4. **User-Friendly Prompts**: Asks for specific missing information

### Required Fields

- Restaurant ID/Name
- User Name
- Phone Number (10+ digits)
- Booking Date (YYYY-MM-DD)
- Booking Time (HH:MM)
- Number of Guests

### Example Flow

**Turn 1: Search**
```
User: "Find Indian restaurants in San Francisco"
Agent: [Shows list of restaurants]
```

**Turn 2: Initial Booking Request**
```
User: "Book Curry Leaf"
Agent: "To complete your booking, I need: your name, phone number, booking date, booking time, and number of guests."
```

**Turn 3: Provide Some Info**
```
User: "My name is John Smith, phone 5551234567"
Agent: "To complete your booking, I need: booking date, booking time, and number of guests."
```

**Turn 4: Provide Remaining Info**
```
User: "Book for 4 people on 2026-03-15 at 19:00"
Agent: "✅ Booking Confirmed! Booking ID: booking_xxx..."
```

## Usage with Streamlit

The Streamlit app (`frontend/app.py`) maintains session state across turns, making incremental booking work seamlessly:

```bash
cd frontend
streamlit run app.py
```

1. Enter your User ID and Phone Number in the sidebar
2. Search for restaurants
3. Request a booking (can provide partial info)
4. Continue conversation until all details are collected
5. Booking executes automatically when all fields are present

## Technical Implementation

### State Management

- `partial_booking_params` in workflow state accumulates information across turns
- Each turn merges new extracted params with existing ones
- Only non-null/non-empty values update the accumulated state

### Parameter Extraction

```python
# Booking agent extracts params and merges with previous turns
params = context.get("partial_params", {}).copy()
new_params = extract_from_llm(user_message)
for key, value in new_params.items():
    if value:  # Only update if not None/empty
        params[key] = value
```

### Missing Field Check

```python
required = ["restaurantId", "userName", "userMobileNo", "date", "time", "noOfGuests"]
missing = [field for field in required if not params.get(field)]
if missing:
    return {"missing_fields": missing, "content": prompt_user(missing)}
```

## Testing

### With Streamlit (Recommended)
```bash
cd frontend
streamlit run app.py
```
This maintains state properly across conversation turns.

### Direct Workflow Test
```bash
python3 tests/test_complete_info.py
```
Provides all information in a single message.

## Limitations

- Each `workflow.invoke()` call creates a new state
- For multi-turn conversations, use Streamlit or implement session persistence
- AgentCore Memory retrieval helps but doesn't replace proper state management

## Future Enhancements

- Persist workflow state in DynamoDB between invocations
- Add conversation context window (last N turns)
- Support editing previously provided information
- Add confirmation step before final booking
