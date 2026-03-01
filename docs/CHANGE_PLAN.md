# Change Plan: Stateless Orchestration Implementation

## Objective
Remove UI state dependencies (`restaurants`, `selected_restaurant`) from orchestrator and workflow. Make backend fully stateless by storing/retrieving all context from AgentCore Memory.

---

## Files to Modify

### 1. `src/orchestrator.py`
### 2. `src/workflows/restaurant_workflow.py`

---

## Detailed Changes

### File 1: `src/orchestrator.py`

#### Change 1.1: Remove UI State Parameters
**Location:** Line ~30-32 (handler function)

**Current Code:**
```python
restaurants = payload.get("restaurants", [])
selected_restaurant = payload.get("selectedRestaurant")
```

**New Code:**
```python
# REMOVED - All context retrieved from AgentCore Memory
```

**Reason:** Backend should not receive UI state. All context comes from memory.

---

#### Change 1.2: Simplify Workflow Invocation
**Location:** Line ~50-56 (workflow.invoke call)

**Current Code:**
```python
result = workflow.invoke(
    user_message=user_message,
    user_id=user_id,
    session_id=session_id,
    restaurants=restaurants,
    selected_restaurant=selected_restaurant,
    is_first_message=False
)
```

**New Code:**
```python
result = workflow.invoke(
    user_message=user_message,
    user_id=user_id,
    session_id=session_id,
    is_first_message=False
)
```

**Reason:** Only pass essential parameters. Context retrieved from memory inside workflow.

---

#### Change 1.3: Remove Restaurants from Response Metadata
**Location:** Line ~65-70 (return statement)

**Current Code:**
```python
return {
    "response": response_text,
    "metadata": {
        "user_id": user_id,
        "session_id": session_id,
        "intent": result.get("intent"),
        "booking_id": result.get("booking_id"),
        "restaurants": result.get("restaurants", []),
        "selected_restaurant": result.get("selected_restaurant")
    }
}
```

**New Code:**
```python
return {
    "response": response_text,
    "metadata": {
        "user_id": user_id,
        "session_id": session_id,
        "intent": result.get("intent"),
        "booking_id": result.get("booking_id")
    }
}
```

**Reason:** UI doesn't need restaurant data. Backend manages all state.

---

### File 2: `src/workflows/restaurant_workflow.py`

#### Change 2.1: Update invoke() Method Signature
**Location:** Line ~380 (invoke method definition)

**Current Code:**
```python
def invoke(self, user_message: str, user_id: str, session_id: str, 
           restaurants: list = None, selected_restaurant: dict = None, 
           phone: str = None, is_first_message: bool = False) -> Dict[str, Any]:
```

**New Code:**
```python
def invoke(self, user_message: str, user_id: str, session_id: str, 
           is_first_message: bool = False) -> Dict[str, Any]:
```

**Reason:** Remove UI state parameters. Phone number not needed (can be in user profile).

---

#### Change 2.2: Update invoke() Docstring
**Location:** Line ~382-395 (invoke method docstring)

**Current Code:**
```python
"""
Invoke workflow with user message.
Retrieves conversation history from AgentCore Memory.

Args:
    user_message: User's input message
    user_id: User identifier (actorId)
    session_id: Session identifier (used as correlation_id for tracing)
    restaurants: Restaurant list from previous search (from Streamlit session)
    selected_restaurant: Selected restaurant (from Streamlit session)
    phone: User phone number
    is_first_message: Whether this is the first message (trigger greeting)

Returns:
    Final state with response
"""
```

**New Code:**
```python
"""
Invoke workflow with user message.
Retrieves ALL context from AgentCore Memory (stateless design).

Args:
    user_message: User's input message
    user_id: User identifier (actorId)
    session_id: Session identifier (used as correlation_id for tracing)
    is_first_message: Whether this is the first message (trigger greeting)

Returns:
    Final state with response
"""
```

**Reason:** Update documentation to reflect stateless design.

---

#### Change 2.3: Simplify Greeting Logic
**Location:** Line ~398-400 (greeting logic)

**Current Code:**
```python
if is_first_message:
    greeting = self.greeting_agent.greet(user_id, phone or "")
    return {"final_response": greeting, "is_greeting": True}
```

**New Code:**
```python
if is_first_message:
    greeting = self.greeting_agent.greet(user_id, "")
    return {"final_response": greeting, "is_greeting": True}
```

**Reason:** Remove phone parameter (not needed for greeting).

---

#### Change 2.4: Remove UI State from Initial Context
**Location:** Line ~403-420 (memory retrieval and context building)

**Current Code:**
```python
memory_data = self._retrieve_memory(user_id, session_id)
memory_params = memory_data.get('booking_params', {})
conversation_history = memory_data.get('conversation_history', '')
booking_completed = memory_data.get('booking_completed', False)

# Always build context with conversation history
initial_context = {
    'selected_restaurant': selected_restaurant,  # ❌ From UI
    'conversation_history': conversation_history,
    'booking_completed': booking_completed,
}
if memory_params:
    initial_context['partial_params'] = memory_params
```

**New Code:**
```python
memory_data = self._retrieve_memory(user_id, session_id)
memory_params = memory_data.get('booking_params', {})
conversation_history = memory_data.get('conversation_history', '')
booking_completed = memory_data.get('booking_completed', False)
restaurants = memory_data.get('restaurants', [])  # ✅ From memory
selected_restaurant = memory_data.get('selected_restaurant')  # ✅ From memory

# Build context from memory ONLY
initial_context = {
    'conversation_history': conversation_history,
    'booking_completed': booking_completed,
}
if selected_restaurant:
    initial_context['selected_restaurant'] = selected_restaurant
if memory_params:
    initial_context['partial_params'] = memory_params
```

**Reason:** All context comes from memory, not UI.

---

#### Change 2.5: Remove UI State from Initial State
**Location:** Line ~423-440 (initial state creation)

**Current Code:**
```python
initial_state = RestaurantBookingState(
    correlation_id=session_id,
    user_id=user_id,
    session_id=session_id,
    messages=[HumanMessage(content=user_message)],
    intent=None,
    confidence=None,
    restaurants=restaurants or [],  # ❌ From UI
    selected_restaurant_id=selected_restaurant.get('restaurantId') if selected_restaurant else None,  # ❌ From UI
    booking_params=None,
    partial_booking_params=memory_params,
    booking_id=None,
    token_amount=None,
    compensation_stack=[],
    hitl_required=False,
    hitl_reason=None,
    error=None,
    retry_count=0,
    current_agent=None,
    next_agent=None,
    context=initial_context,
    final_response=None
)
```

**New Code:**
```python
initial_state = RestaurantBookingState(
    correlation_id=session_id,
    user_id=user_id,
    session_id=session_id,
    messages=[HumanMessage(content=user_message)],
    intent=None,
    confidence=None,
    restaurants=restaurants,  # ✅ From memory
    selected_restaurant_id=selected_restaurant.get('restaurantId') if selected_restaurant else None,  # ✅ From memory
    booking_params=None,
    partial_booking_params=memory_params,
    booking_id=None,
    token_amount=None,
    compensation_stack=[],
    hitl_required=False,
    hitl_reason=None,
    error=None,
    retry_count=0,
    current_agent=None,
    next_agent=None,
    context=initial_context,
    final_response=None
)
```

**Reason:** Use restaurants from memory instead of UI.

---

#### Change 2.6: Update _retrieve_memory() to Include Restaurants
**Location:** Line ~470-520 (_retrieve_memory method)

**Current Code:**
```python
def _retrieve_memory(self, user_id: str, session_id: str) -> Dict[str, Any]:
    """Retrieve booking state AND full conversation history from AgentCore Memory"""
    if not self.memory_id:
        return {'booking_params': {}, 'conversation_history': '', 'booking_completed': False}
    
    try:
        response = self.memory_client.list_events(...)
        
        # Extract booking params
        booking_params = {}
        booking_completed = False
        for event in reversed(events):
            # ... extract booking_params and booking_completed
        
        # Build conversation history
        conversation_turns = []
        for event in events:
            # ... build conversation history
        
        return {
            'booking_params': booking_params,
            'conversation_history': conversation_history,
            'booking_completed': booking_completed
        }
    except Exception as e:
        return {'booking_params': {}, 'conversation_history': '', 'booking_completed': False}
```

**New Code:**
```python
def _retrieve_memory(self, user_id: str, session_id: str) -> Dict[str, Any]:
    """Retrieve ALL context from AgentCore Memory: conversation, restaurants, booking state"""
    if not self.memory_id:
        return {
            'booking_params': {}, 
            'conversation_history': '', 
            'booking_completed': False,
            'restaurants': [],
            'selected_restaurant': None
        }
    
    try:
        response = self.memory_client.list_events(...)
        
        import json
        import base64
        events = response.get('events', [])
        
        # Extract ALL context
        booking_params = {}
        booking_completed = False
        restaurants = []
        selected_restaurant = None
        
        for event in reversed(events):
            metadata = event.get('metadata', {})
            
            # Extract restaurants (from last search)
            if 'restaurants_b64' in metadata and not restaurants:
                try:
                    rest_b64 = metadata['restaurants_b64'].get('stringValue', '')
                    restaurants = json.loads(base64.b64decode(rest_b64).decode())
                except: pass
            
            # Extract selected restaurant
            if 'selected_restaurant_b64' in metadata and not selected_restaurant:
                try:
                    sel_b64 = metadata['selected_restaurant_b64'].get('stringValue', '')
                    selected_restaurant = json.loads(base64.b64decode(sel_b64).decode())
                except: pass
            
            # Extract booking params
            if 'booking_params_b64' in metadata:
                try:
                    params_b64 = metadata['booking_params_b64'].get('stringValue', '')
                    booking_params = json.loads(base64.b64decode(params_b64).decode())
                except: pass
            
            # Check booking completion
            if 'booking_completed' in metadata:
                booking_completed = metadata['booking_completed'].get('stringValue') == 'true'
            
            if booking_completed:
                break
        
        # Build conversation history
        conversation_turns = []
        for event in events:
            for item in event.get('payload', []):
                if 'conversational' in item:
                    role = item['conversational']['role']
                    text = item['conversational']['content']['text']
                    conversation_turns.append(f"{role}: {text}")
        
        conversation_history = "\n".join(conversation_turns)
        
        return {
            'booking_params': booking_params,
            'conversation_history': conversation_history,
            'booking_completed': booking_completed,
            'restaurants': restaurants,
            'selected_restaurant': selected_restaurant
        }
    
    except Exception as e:
        print(f"[DEBUG] Memory retrieval exception: {e}")
        return {
            'booking_params': {}, 
            'conversation_history': '', 
            'booking_completed': False,
            'restaurants': [],
            'selected_restaurant': None
        }
```

**Reason:** Retrieve restaurant data from memory instead of expecting it from UI.

---

#### Change 2.7: Update _store_memory() to Store Restaurants
**Location:** Line ~525-570 (_store_memory method)

**Current Code:**
```python
def _store_memory(self, user_id: str, session_id: str, 
                  user_message: str, assistant_response: str,
                  intent: str, metadata: Dict[str, Any]):
    """Store conversation turn and booking state in AgentCore Memory"""
    if not self.memory_id or not assistant_response:
        return
    
    try:
        import datetime, base64, json
        
        # Build metadata with booking state
        memory_metadata = {'intent': {'stringValue': intent or 'unknown'}}
        
        # Only store booking params when booking SUCCEEDS
        if metadata.get('booking_id'):
            memory_metadata['booking_id'] = {'stringValue': metadata['booking_id']}
            memory_metadata['booking_completed'] = {'stringValue': 'true'}
            if metadata.get('partial_booking_params'):
                params_json = json.dumps(metadata['partial_booking_params'])
                params_b64 = base64.b64encode(params_json.encode()).decode()
                memory_metadata['booking_params_b64'] = {'stringValue': params_b64}
        
        self.memory_client.create_event(...)
    except Exception as e:
        print(f"Memory storage error: {e}")
```

**New Code:**
```python
def _store_memory(self, user_id: str, session_id: str, 
                  user_message: str, assistant_response: str,
                  intent: str, metadata: Dict[str, Any]):
    """Store conversation turn, restaurant data, and booking state in AgentCore Memory"""
    if not self.memory_id or not assistant_response:
        return
    
    try:
        import datetime, base64, json
        
        # Build metadata with ALL context
        memory_metadata = {'intent': {'stringValue': intent or 'unknown'}}
        
        # Store restaurant search results (if any)
        if metadata.get('restaurants'):
            restaurants_json = json.dumps(metadata['restaurants'])
            restaurants_b64 = base64.b64encode(restaurants_json.encode()).decode()
            memory_metadata['restaurants_b64'] = {'stringValue': restaurants_b64}
        
        # Store selected restaurant (if any)
        if metadata.get('selected_restaurant'):
            selected_json = json.dumps(metadata['selected_restaurant'])
            selected_b64 = base64.b64encode(selected_json.encode()).decode()
            memory_metadata['selected_restaurant_b64'] = {'stringValue': selected_b64}
        
        # Store booking params when booking SUCCEEDS
        if metadata.get('booking_id'):
            memory_metadata['booking_id'] = {'stringValue': metadata['booking_id']}
            memory_metadata['booking_completed'] = {'stringValue': 'true'}
            if metadata.get('partial_booking_params'):
                params_json = json.dumps(metadata['partial_booking_params'])
                params_b64 = base64.b64encode(params_json.encode()).decode()
                memory_metadata['booking_params_b64'] = {'stringValue': params_b64}
        
        self.memory_client.create_event(...)
    except Exception as e:
        print(f"Memory storage error: {e}")
```

**Reason:** Store restaurant data in memory so it can be retrieved in next turn.

---

#### Change 2.8: Update _booking_agent_node() Restaurant Resolution
**Location:** Line ~195-230 (_booking_agent_node method)

**Current Code:**
```python
# Use LLM to extract restaurant from conversation history
if context.get("selected_restaurant"):
    context["restaurants"] = [context["selected_restaurant"]]
elif context.get("conversation_history") and state.get("restaurants"):
    # Let LLM extract restaurant from conversation
    from src.core import AmazonNovaProvider
    bedrock = AmazonNovaProvider("amazon.nova-lite-v1:0")
    restaurant_list = "\n".join([f"{r.get('name')} (ID: {r.get('restaurantId')})" for r in state["restaurants"]])
    match_prompt = f"""Extract restaurant ID from conversation...
    
Available restaurants:
{restaurant_list}

Which restaurant is mentioned? Return ONLY the restaurant ID."""
    # ... rest of LLM extraction logic
elif state.get("restaurants"):
    context["restaurants"] = state["restaurants"]
```

**New Code:**
```python
# Resolve restaurant from context (already loaded from memory)
if context.get("selected_restaurant"):
    context["restaurants"] = [context["selected_restaurant"]]
    print(f"[DEBUG] Using selected_restaurant from memory: {context['selected_restaurant'].get('name')}")
elif state.get("restaurants"):
    # Restaurants already loaded from memory in initial_state
    context["restaurants"] = state["restaurants"]
    print(f"[DEBUG] Using restaurants from memory: {len(context['restaurants'])} found")
    
    # If multiple restaurants, use LLM to extract which one user wants
    if len(context["restaurants"]) > 1 and context.get("conversation_history"):
        from src.core import AmazonNovaProvider
        bedrock = AmazonNovaProvider("amazon.nova-lite-v1:0")
        restaurant_list = "\n".join([f"{r.get('name')} (ID: {r.get('restaurantId')})" for r in context["restaurants"]])
        match_prompt = f"""Extract restaurant ID from conversation.

Conversation:
{context['conversation_history']}

Current message: {user_message}

Available restaurants:
{restaurant_list}

Which restaurant is mentioned? Return ONLY the restaurant ID."""
        
        try:
            match_response = bedrock.invoke(
                messages=[{"role": "user", "content": [{"text": match_prompt}]}],
                temperature=0.0,
                max_tokens=50
            )
            matched_id = match_response["content"].strip()
            for rest in context["restaurants"]:
                if rest.get("restaurantId") == matched_id:
                    context["restaurants"] = [rest]
                    print(f"[DEBUG] LLM extracted from conversation: {rest.get('name')}")
                    break
        except Exception as e:
            print(f"[DEBUG] LLM extraction error: {e}")
```

**Reason:** Simplify logic since restaurants already loaded from memory.

---

## Summary of Changes

### Orchestrator (`src/orchestrator.py`)
1. ✅ Remove `restaurants` and `selected_restaurant` from payload extraction
2. ✅ Remove these parameters from `workflow.invoke()` call
3. ✅ Remove `restaurants` and `selected_restaurant` from response metadata

### Workflow (`src/workflows/restaurant_workflow.py`)
1. ✅ Update `invoke()` signature - remove `restaurants`, `selected_restaurant`, `phone`
2. ✅ Update `invoke()` docstring
3. ✅ Remove `phone` from greeting call
4. ✅ Load `restaurants` and `selected_restaurant` from memory
5. ✅ Use memory data in initial context
6. ✅ Use memory data in initial state
7. ✅ Update `_retrieve_memory()` to extract restaurants
8. ✅ Update `_store_memory()` to store restaurants
9. ✅ Simplify `_booking_agent_node()` restaurant resolution

---

## Testing Plan

### Test 1: Restaurant Search
```
User: "Find Italian restaurants in Seattle"
Expected: 
- Restaurants stored in AgentCore Memory
- Response shows restaurant list
```

### Test 2: Multi-Turn Booking
```
Turn 1: "Find Italian restaurants in Seattle"
Turn 2: "Book the first one for tomorrow at 7pm"
Expected:
- Restaurants retrieved from memory
- LLM extracts restaurant from conversation
- Booking succeeds
```

### Test 3: Session Continuity
```
Session 1: "Find Italian restaurants in Seattle"
Session 2 (same user): "Book the first one"
Expected:
- Restaurants retrieved from memory
- Booking succeeds without re-searching
```

---

## Rollback Plan

If issues occur:
1. Revert `src/orchestrator.py` to pass `restaurants` and `selected_restaurant`
2. Revert `src/workflows/restaurant_workflow.py` invoke signature
3. Keep memory storage changes (backward compatible)

---

## Review Questions

1. ✅ Do you approve removing `restaurants` and `selected_restaurant` from orchestrator?
2. ✅ Do you approve storing restaurant data in AgentCore Memory?
3. ✅ Do you approve the LLM-based restaurant extraction from conversation?
4. ✅ Should we keep `phone` parameter or remove it?
5. ✅ Any other concerns or suggestions?

---

## Next Steps

After approval:
1. Implement changes in order listed above
2. Test each change incrementally
3. Run integration tests
4. Update documentation
5. Deploy to dev environment for validation
