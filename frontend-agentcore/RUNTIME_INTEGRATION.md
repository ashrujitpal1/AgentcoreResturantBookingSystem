# Streamlit Frontend - AgentCore Runtime Integration

## ✅ Updated to Use Deployed Runtime

The Streamlit frontend (`frontend-agentcore/app.py`) has been updated to invoke the **deployed AgentCore Runtime** instead of running locally.

---

## Changes Made

### Before (Local Execution)
```python
from src.orchestrator import handler

# Called handler directly
result = handler(event, MockContext())
```

### After (Deployed Runtime)
```python
from bedrock_agentcore_starter_toolkit import Runtime

# Initialize Runtime SDK
runtime = Runtime()

# Invoke deployed runtime
response = runtime.invoke(
    runtime_id=RUNTIME_ID,
    input_data={
        "inputText": enhanced_prompt,
        "userId": st.session_state.user_id,
        "sessionId": st.session_state.session_id
    }
)
```

---

## Configuration

The app now reads the deployed runtime ARN from `.env`:

```bash
AGENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:696072349808:runtime/restaurant_booking_orchestrator-JZpyQwCgEq
```

Runtime ID is automatically extracted: `restaurant_booking_orchestrator-JZpyQwCgEq`

---

## How to Run

```bash
cd frontend-agentcore
streamlit run app.py
```

The app will now:
1. ✅ Read `AGENT_RUNTIME_ARN` from `.env`
2. ✅ Initialize Runtime SDK
3. ✅ Invoke the deployed AgentCore Runtime
4. ✅ Display responses from the cloud-deployed agent

---

## Benefits

✅ **Production Deployment** - Uses actual deployed runtime  
✅ **Scalability** - Runtime auto-scales based on load  
✅ **Observability** - All invocations logged to CloudWatch  
✅ **Consistency** - Same runtime used by all clients  
✅ **No Local Dependencies** - No need to run orchestrator locally  

---

## Testing

1. Ensure `.env` has `AGENT_RUNTIME_ARN`
2. Run: `streamlit run frontend-agentcore/app.py`
3. Enter User ID and Phone Number
4. Test queries:
   - "Find Indian restaurants in New York"
   - "Show me Japanese food"
   - "Book a table at Spice Symphony"

---

## Debug Mode

Enable debug mode in the sidebar to see:
- Runtime ID being invoked
- Session ID
- User ID
- Full response from runtime

---

## Architecture Flow

```
User → Streamlit UI → Runtime SDK → AgentCore Runtime (Cloud)
                                    ↓
                                LangGraph Workflow
                                    ↓
                            Strands Agents + MCP Gateway
                                    ↓
                            Lambda Functions + DynamoDB
```

---

## Status

✅ **Frontend Updated**  
✅ **Runtime Deployed**  
✅ **Integration Complete**  
✅ **Ready for Testing**
