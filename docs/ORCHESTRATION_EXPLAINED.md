# Restaurant Booking System - Orchestration Flow Explained

## Overview
The system uses **LangGraph** for workflow orchestration and **Strands Agents** for individual task execution. This document explains how `orchestrator.py` and `restaurant_workflow.py` work together.

---

## File 1: `orchestrator.py` - Entry Point

### Purpose
Main Lambda handler that receives requests from AWS Bedrock AgentCore Runtime.

### Step-by-Step Flow

#### **Step 1: Handler Invocation**
```python
@app.entrypoint
def handler(payload: dict, context: RequestContext) -> dict:
```
- AWS invokes this function when user sends a message
- Receives `payload` with user input and `context` with session info

#### **Step 2: Extract Request Data**
```python
user_message = payload.get("inputText", "")
user_id = payload.get("userId", "unknown")
session_id = context.session_id or payload.get("sessionId")
restaurants = payload.get("restaurants", [])
selected_restaurant = payload.get("selectedRestaurant")
```
- Extracts user message, IDs, and any existing restaurant data
- Session ID used for conversation tracking

#### **Step 3: Initialize MCP Client**
```python
mcp_client = get_mcp_client()
with mcp_client:
    mcp_tools = mcp_client.list_tools_sync()
```
- Connects to MCP Gateway (Model Context Protocol)
- Retrieves available tools (Lambda functions for restaurant search, booking, payment)
- Tools are idempotent with `requestId` for deduplication

#### **Step 4: Create Workflow Instance**
```python
workflow = RestaurantBookingWorkflow(mcp_tools)
```
- Instantiates LangGraph workflow
- Passes MCP tools to workflow for agent use

#### **Step 5: Invoke Workflow**
```python
result = workflow.invoke(
    user_message=user_message,
    user_id=user_id,
    session_id=session_id,
    restaurants=restaurants,
    selected_restaurant=selected_restaurant
)
```
- Executes the LangGraph state machine
- Returns final state with response

#### **Step 6: Return Response**
```python
return {
    "response": response_text,
    "metadata": {
        "intent": result.get("intent"),
        "booking_id": result.get("booking_id"),
        "restaurants": result.get("restaurants")
    }
}
```
- Formats response for AgentCore Runtime
- Includes metadata for tracking

---

## File 2: `restaurant_workflow.py` - LangGraph Workflow

### Purpose
Orchestrates Strands agents using LangGraph state machine with conditional routing.

---

## Part A: Initialization

### **Step 1: Constructor**
```python
def __init__(self, mcp_tools: Dict[str, Any]):
    self.mcp_tools = mcp_tools
    
    # Initialize Strands agents
    self.greeting_agent = GreetingAgent()
    self.intent_classifier = IntentClassifierAgent()
    self.restaurant_finder = RestaurantFinderAgent(mcp_tools)
    self.booking_agent = BookingAgent(mcp_tools)
    
    # Initialize AgentCore Memory
    self.memory_client = boto3.client('bedrock-agentcore')
    self.memory_id = os.getenv('MEMORY_ID')
```

**What happens:**
1. Stores MCP tools for agent use
2. Creates 4 Strands agents (each handles ONE task - SOLID principle)
3. Initializes AWS Bedrock AgentCore Memory client for conversation persistence

---

### **Step 2: Build Workflow Graph**
```python
def _build_workflow(self) -> StateGraph:
    workflow = StateGraph(RestaurantBookingState)
    
    # Add nodes
    workflow.add_node("entry_router", self._entry_router_node)
    workflow.add_node("restaurant_finder", self._restaurant_finder_node)
    workflow.add_node("booking_agent", self._booking_agent_node)
    workflow.add_node("error_handler", self._error_handler_node)
```

**What happens:**
- Creates LangGraph state machine
- Each node is a Python function that wraps a Strands agent
- Nodes are connected with conditional edges (routing logic)

**Graph Structure:**
```
User Input
    ↓
entry_router (classify intent)
    ↓
    ├─→ restaurant_finder (search) ─→ booking_agent (book)
    ├─→ booking_agent (direct booking)
    └─→ error_handler (errors)
```

---

## Part B: Node Functions (Agent Wrappers)

### **Node 1: Entry Router** (`_entry_router_node`)

#### Purpose
Classify user intent and route to appropriate agent.

#### Step-by-Step:

**1. Extract User Message**
```python
user_message = state["messages"][-1].content
correlation_id = state["correlation_id"]
context = state.get("context") or {}
```

**2. Build Conversation History**
```python
# Combine memory history + current session messages
memory_history = context.get("conversation_history", "")
session_turns = []
for msg in state.get("messages", [])[:-1]:
    if isinstance(msg, HumanMessage):
        session_turns.append(f"USER: {msg.content}")
    elif isinstance(msg, AIMessage):
        session_turns.append(f"ASSISTANT: {msg.content}")
full_history = f"{memory_history}\n{session_history}".strip()
```
- Retrieves past conversation from AgentCore Memory
- Adds current session messages
- Creates full conversation trail for context-aware intent classification

**3. Call Intent Classifier Agent**
```python
result = self.intent_classifier.process(user_message, correlation_id, router_context)
intent = result.get("intent")
```
- Uses Bedrock Converse API with Amazon Nova Micro (cheapest model)
- Returns: `search`, `booking`, `payment`, or `out_of_scope`

**4. Handle Out-of-Scope Requests**
```python
if intent in ["out_of_scope", "invalid", None]:
    return {
        "intent": intent,
        "final_response": "I'm a restaurant booking assistant..."
    }
```
- Immediately rejects non-restaurant queries
- Implements guardrails pattern

**5. Merge Context**
```python
existing_context = state.get("context") or {}
new_context = result.get("extracted_entities", {})
merged_context = {**existing_context, **new_context}
```
- Preserves existing context (e.g., selected restaurant)
- Adds newly extracted entities (city, cuisine, date)

**6. Return Updated State**
```python
return {
    "intent": result.get("intent"),
    "confidence": result.get("confidence"),
    "current_agent": "intent_classifier",
    "context": merged_context
}
```

---

### **Node 2: Restaurant Finder** (`_restaurant_finder_node`)

#### Purpose
Search restaurants using MCP tools and RAG pattern.

#### Step-by-Step:

**1. Call Restaurant Finder Agent**
```python
result = self.restaurant_finder.process(user_message, correlation_id, context)
restaurants = result.get("restaurants", [])
```
- Agent uses Query Rewriter (creates 3-5 variations)
- Hybrid Retriever (vector + keyword search)
- Reranker (ranks by relevance)
- Calls MCP tool: `fetchRestaurantDetails`

**2. Auto-Select Restaurant**
```python
selected_restaurant = None
if len(restaurants) == 1:
    selected_restaurant = restaurants[0]  # Only one found
elif len(state.get("restaurants", [])) > 1:
    # User selecting from previous results
    for r in state["restaurants"]:
        if r.get('name', '').lower() in user_message.lower():
            selected_restaurant = r
            break
```
- If only 1 restaurant found → auto-select
- If multiple exist → check if user mentioned a name

**3. Update State**
```python
return {
    "messages": [ai_message],
    "restaurants": restaurants,
    "selected_restaurant": selected_restaurant,
    "next_agent": result.get("handoff_to"),  # "booking_agent" if ready
    "final_response": result.get("content")
}
```
- Stores restaurant list
- Sets handoff flag if user wants to book

---

### **Node 3: Booking Agent** (`_booking_agent_node`)

#### Purpose
Execute booking with SAGA pattern (transaction safety).

#### Step-by-Step:

**1. Extract Last Human Message**
```python
user_message = None
for msg in reversed(state["messages"]):
    if isinstance(msg, HumanMessage):
        user_message = msg.content
        break
```
- Finds last user input (not AI response)

**2. Resolve Restaurant from Context**
```python
if context.get("selected_restaurant"):
    context["restaurants"] = [context["selected_restaurant"]]
elif context.get("conversation_history") and state.get("restaurants"):
    # Use LLM to extract restaurant from conversation
    bedrock = AmazonNovaProvider("amazon.nova-lite-v1:0")
    match_prompt = f"Extract restaurant ID from conversation..."
    match_response = bedrock.invoke(messages=[...])
    matched_id = match_response["content"].strip()
```
- First checks if restaurant already selected
- If not, uses LLM to extract from conversation history
- Prevents "which restaurant?" errors

**3. Load Partial Booking Params from Memory**
```python
if state.get("partial_booking_params"):
    context["partial_params"] = state["partial_booking_params"]
```
- Retrieves previously collected booking details (date, time, guests)
- Enables multi-turn booking conversations

**4. Build Full Conversation History**
```python
memory_history = context.get("conversation_history", "")
session_turns = []
for msg in state.get("messages", []):
    if isinstance(msg, HumanMessage):
        session_turns.append(f"USER: {msg.content}")
    elif isinstance(msg, AIMessage):
        session_turns.append(f"ASSISTANT: {msg.content}")
context["conversation_history"] = f"{memory_history}\n{session_history}".strip()
```
- Combines memory + session messages
- Agent uses this to extract booking parameters

**5. Call Booking Agent (SAGA Pattern)**
```python
result = self.booking_agent.process(user_message, correlation_id, context)
```

**Inside BookingAgent (SAGA workflow):**
```python
compensation_stack = []
try:
    # Step 1: Validate availability
    availability = check_availability_tool(...)
    compensation_stack.append(("release_hold", availability["hold_id"]))
    
    # Step 2: Create booking
    booking = create_booking_tool(...)
    compensation_stack.append(("cancel_booking", booking["booking_id"]))
    
    # Step 3: Process payment
    payment = process_payment_tool(...)
    compensation_stack.append(("refund_payment", payment["transaction_id"]))
    
    return {"success": True, "booking_id": booking["booking_id"]}
except Exception as e:
    # Rollback in reverse order
    for operation, resource_id in reversed(compensation_stack):
        compensate(operation, resource_id)
    raise
```

**6. Handle Missing Fields**
```python
if result.get("missing_fields"):
    accumulated_params = state.get("partial_booking_params") or {}
    new_params = result.get("partial_params", {})
    for key, value in new_params.items():
        if value:
            accumulated_params[key] = value
    
    return {
        "final_response": result.get("content"),  # "What date would you like?"
        "partial_booking_params": accumulated_params
    }
```
- If booking params incomplete → ask user for missing info
- Accumulates params across multiple turns

**7. Handle HITL (Human-in-the-Loop)**
```python
if result.get("hitl_required"):
    return {
        "hitl_required": True,
        "hitl_reason": result.get("reason"),
        "final_response": f"⚠️ Approval Required: {result.get('reason')}"
    }
```
- Flags bookings requiring manual approval (e.g., large party, special requests)

**8. Handle Success**
```python
if result.get("success"):
    updated_context = state.get("context", {})
    updated_context["booking_completed"] = True  # Prevent duplicate bookings
    
    return {
        "booking_id": result.get("booking_details", {}).get("booking_id"),
        "token_amount": result.get("booking_details", {}).get("token_amount"),
        "compensation_stack": result.get("compensation_log", []),
        "context": updated_context,
        "final_response": result.get("content")
    }
```
- Marks booking as completed
- Stores compensation log for audit

---

### **Node 4: Error Handler** (`_error_handler_node`)

#### Purpose
Handle errors with SAGA compensation rollback.

```python
def _error_handler_node(self, state: RestaurantBookingState) -> Dict[str, Any]:
    error = state.get("error", "Unknown error")
    compensation_log = state.get("compensation_stack", [])
    
    error_message = f"""❌ An error occurred: {error}

Rollback actions taken:
{chr(10).join(compensation_log) if compensation_log else 'None'}"""
    
    return {"final_response": error_message}
```
- Shows user what went wrong
- Lists rollback actions taken (SAGA pattern)

---

## Part C: Routing Functions

### **Router 1: Route by Intent**
```python
def _route_by_intent(self, state: RestaurantBookingState) -> Literal["search", "booking", "error"]:
    intent = state.get("intent")
    
    if intent in ["out_of_scope", "invalid", None]:
        return "error"
    if intent == "search":
        return "search"
    elif intent in ["booking", "payment"]:
        return "booking"
    else:
        return "search"  # Default
```

### **Router 2: Route After Search**
```python
def _route_after_search(self, state: RestaurantBookingState) -> Literal["booking", "end"]:
    next_agent = state.get("next_agent")
    
    if next_agent == "booking_agent":
        return "booking"  # User wants to book
    else:
        return "end"  # Just showing results
```

### **Router 3: Route After Booking**
```python
def _route_after_booking(self, state: RestaurantBookingState) -> Literal["error", "end"]:
    if state.get("error"):
        return "error"
    else:
        return "end"
```

---

## Part D: Public API

### **Main Invoke Method**

```python
def invoke(self, user_message: str, user_id: str, session_id: str, 
           restaurants: list = None, selected_restaurant: dict = None, 
           is_first_message: bool = False) -> Dict[str, Any]:
```

#### Step-by-Step:

**1. Handle First Message (Greeting)**
```python
if is_first_message:
    greeting = self.greeting_agent.greet(user_id, phone or "")
    return {"final_response": greeting, "is_greeting": True}
```

**2. Retrieve Memory**
```python
memory_data = self._retrieve_memory(user_id, session_id)
memory_params = memory_data.get('booking_params', {})
conversation_history = memory_data.get('conversation_history', '')
booking_completed = memory_data.get('booking_completed', False)
```
- Fetches conversation history from AgentCore Memory
- Retrieves partial booking params
- Checks if booking already completed (prevents duplicates)

**3. Build Initial Context**
```python
initial_context = {
    'selected_restaurant': selected_restaurant,
    'conversation_history': conversation_history,
    'booking_completed': booking_completed,
}
if memory_params:
    initial_context['partial_params'] = memory_params
```

**4. Initialize State**
```python
initial_state = RestaurantBookingState(
    correlation_id=session_id,
    user_id=user_id,
    messages=[HumanMessage(content=user_message)],
    restaurants=restaurants or [],
    partial_booking_params=memory_params,
    context=initial_context
)
```

**5. Execute Workflow**
```python
final_state = self.app.invoke(initial_state)
```
- Runs LangGraph state machine
- Executes nodes based on routing logic

**6. Store Memory**
```python
self._store_memory(
    user_id=user_id,
    session_id=session_id,
    user_message=user_message,
    assistant_response=final_state.get("final_response", ""),
    intent=final_state.get("intent"),
    metadata=final_state
)
```
- Saves conversation turn to AgentCore Memory
- Stores booking params if booking completed

**7. Return Final State**
```python
return final_state
```

---

## Part E: Memory Management

### **Retrieve Memory** (`_retrieve_memory`)

```python
def _retrieve_memory(self, user_id: str, session_id: str) -> Dict[str, Any]:
    response = self.memory_client.list_events(
        memoryId=self.memory_id,
        actorId=user_id,
        sessionId=session_id,
        maxResults=10
    )
    
    events = response.get('events', [])
```

**What it does:**
1. Fetches last 10 conversation events from AgentCore Memory
2. Extracts booking params (base64 encoded)
3. Checks if booking already completed
4. Builds full conversation history

**Returns:**
```python
{
    'booking_params': {...},  # Partial booking details
    'conversation_history': "USER: ...\nASSISTANT: ...",
    'booking_completed': False
}
```

---

### **Store Memory** (`_store_memory`)

```python
def _store_memory(self, user_id: str, session_id: str, 
                  user_message: str, assistant_response: str,
                  intent: str, metadata: Dict[str, Any]):
    
    memory_metadata = {'intent': {'stringValue': intent or 'unknown'}}
    
    # Only store booking params on SUCCESS
    if metadata.get('booking_id'):
        memory_metadata['booking_id'] = {'stringValue': metadata['booking_id']}
        memory_metadata['booking_completed'] = {'stringValue': 'true'}
        
        if metadata.get('partial_booking_params'):
            params_json = json.dumps(metadata['partial_booking_params'])
            params_b64 = base64.b64encode(params_json.encode()).decode()
            memory_metadata['booking_params_b64'] = {'stringValue': params_b64}
    
    self.memory_client.create_event(
        memoryId=self.memory_id,
        actorId=user_id,
        sessionId=session_id,
        payload=[
            {'conversational': {'content': {'text': user_message}, 'role': 'USER'}},
            {'conversational': {'content': {'text': assistant_response}, 'role': 'ASSISTANT'}}
        ],
        metadata=memory_metadata
    )
```

**What it does:**
1. Creates event in AgentCore Memory
2. Stores user message + assistant response
3. Stores booking params (base64 encoded) ONLY on success
4. Flags booking as completed to prevent duplicates

---

## Complete Flow Example

### User: "Find Italian restaurants in Seattle"

1. **orchestrator.py** receives request
2. **entry_router_node** → Intent Classifier → `intent = "search"`
3. **Router** → Routes to `restaurant_finder`
4. **restaurant_finder_node** → Calls MCP tool → Returns 3 restaurants
5. **Router** → Routes to `END` (no booking requested)
6. **Memory** → Stores conversation
7. **Response** → "I found 3 Italian restaurants in Seattle..."

### User: "Book the first one for tomorrow at 7pm, 2 people"

1. **orchestrator.py** receives request
2. **Memory** → Retrieves conversation history + restaurant list
3. **entry_router_node** → Intent Classifier → `intent = "booking"`
4. **Router** → Routes to `booking_agent`
5. **booking_agent_node** → Extracts params → Calls MCP tools (SAGA):
   - Check availability ✓
   - Create booking ✓
   - Process payment ✓
6. **Router** → Routes to `END`
7. **Memory** → Stores booking_id + marks completed
8. **Response** → "✅ Booking confirmed! ID: BK123..."

---

## Key Design Patterns

### 1. **Handoff Pattern**
- Restaurant Finder → Booking Agent
- Context transferred between agents

### 2. **SAGA Pattern**
- Booking Agent executes compensatable transactions
- Rollback on failure

### 3. **Circuit Breaker**
- Primary LLM (Claude) → Fallback (Nova)

### 4. **Idempotency**
- All MCP tool calls include `requestId`
- Prevents duplicate bookings

### 5. **Memory Pattern**
- AgentCore Memory stores conversation + state
- Enables multi-turn conversations

### 6. **Guardrails Pattern**
- Input validation (prompt injection)
- Scope validation (out-of-scope rejection)

---

## Summary

**orchestrator.py**: Entry point that initializes MCP client and invokes workflow

**restaurant_workflow.py**: LangGraph state machine that:
1. Classifies intent
2. Routes to appropriate agent
3. Executes agent logic
4. Manages conversation memory
5. Handles errors with SAGA compensation

**Result**: Production-grade agentic system with conversation persistence, transaction safety, and cost optimization.
