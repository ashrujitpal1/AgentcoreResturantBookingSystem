# Corrected Orchestration Flow - Stateless Design

## Problem Statement

**Current Implementation (WRONG):**
- Orchestrator receives `restaurants` and `selected_restaurant` from payload
- UI (Streamlit) maintains state and passes it to backend
- Violates stateless principle and creates tight coupling

**Your Understanding (CORRECT):**
- Orchestrator should ONLY receive `user_id`, `session_id`, and `user_message`
- All context should be retrieved from AgentCore Memory
- LLM extracts restaurant details from conversation history

---

## Corrected Implementation

### 1. Orchestrator (orchestrator.py)

```python
@app.entrypoint
def handler(payload: dict, context: RequestContext) -> dict:
    """
    Stateless handler - only extracts user message and IDs.
    All context retrieved from AgentCore Memory.
    """
    # ✅ ONLY extract these 3 things
    user_message = payload.get("inputText", "")
    user_id = payload.get("userId", "unknown")
    session_id = (context.session_id if context and context.session_id
                  else payload.get("sessionId") or f"session_{os.urandom(8).hex()}")
    
    # ❌ REMOVE THESE LINES
    # restaurants = payload.get("restaurants", [])  # DELETE
    # selected_restaurant = payload.get("selectedRestaurant")  # DELETE
    
    try:
        mcp_client = get_mcp_client()
        with mcp_client:
            mcp_tools = mcp_client.list_tools_sync()
            workflow = RestaurantBookingWorkflow(mcp_tools)
            
            # ✅ ONLY pass user_message, user_id, session_id
            result = workflow.invoke(
                user_message=user_message,
                user_id=user_id,
                session_id=session_id
                # ❌ REMOVE: restaurants=restaurants
                # ❌ REMOVE: selected_restaurant=selected_restaurant
            )
            
            return {
                "response": result.get("final_response", ""),
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "intent": result.get("intent"),
                    "booking_id": result.get("booking_id")
                    # ✅ Don't return restaurants - UI doesn't need them
                }
            }
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        return {
            "response": "I encountered an error. Please try again.",
            "error": str(e)
        }
```

---

### 2. Workflow Invoke Method (restaurant_workflow.py)

```python
def invoke(self, user_message: str, user_id: str, session_id: str, 
           is_first_message: bool = False) -> Dict[str, Any]:
    """
    Stateless invoke - retrieves ALL context from AgentCore Memory.
    
    Args:
        user_message: User's input message
        user_id: User identifier
        session_id: Session identifier
        is_first_message: Whether this is first message (for greeting)
    
    Returns:
        Final state with response
    """
    # ✅ Handle greeting
    if is_first_message:
        greeting = self.greeting_agent.greet(user_id, "")
        return {"final_response": greeting, "is_greeting": True}
    
    # ✅ Retrieve EVERYTHING from AgentCore Memory
    memory_data = self._retrieve_memory(user_id, session_id)
    
    # ✅ Extract all context from memory
    conversation_history = memory_data.get('conversation_history', '')
    partial_booking_params = memory_data.get('booking_params', {})
    booking_completed = memory_data.get('booking_completed', False)
    
    # ✅ Build initial context from memory ONLY
    initial_context = {
        'conversation_history': conversation_history,
        'booking_completed': booking_completed,
    }
    if partial_booking_params:
        initial_context['partial_params'] = partial_booking_params
    
    # ✅ Initialize state WITHOUT restaurants/selected_restaurant
    initial_state = RestaurantBookingState(
        correlation_id=session_id,
        user_id=user_id,
        session_id=session_id,
        messages=[HumanMessage(content=user_message)],
        intent=None,
        confidence=None,
        restaurants=[],  # ✅ Empty - will be populated by agent
        selected_restaurant_id=None,  # ✅ None - will be extracted from conversation
        partial_booking_params=partial_booking_params,
        context=initial_context
    )
    
    # ✅ Execute workflow
    final_state = self.app.invoke(initial_state)
    
    # ✅ Store conversation in memory
    self._store_memory(
        user_id=user_id,
        session_id=session_id,
        user_message=user_message,
        assistant_response=final_state.get("final_response", ""),
        intent=final_state.get("intent"),
        metadata=final_state
    )
    
    return final_state
```

---

### 3. Restaurant Finder Node (restaurant_workflow.py)

```python
def _restaurant_finder_node(self, state: RestaurantBookingState) -> Dict[str, Any]:
    """
    Search restaurants - results stored in STATE and MEMORY.
    No need to pass back to UI.
    """
    user_message = state["messages"][-1].content
    correlation_id = state["correlation_id"]
    context = state.get("context")
    
    # ✅ Call agent to search
    result = self.restaurant_finder.process(user_message, correlation_id, context)
    restaurants = result.get("restaurants", [])
    
    # ✅ Auto-select if only 1 restaurant
    selected_restaurant = None
    if len(restaurants) == 1:
        selected_restaurant = restaurants[0]
    
    # ✅ Store in STATE (will be persisted to memory)
    return {
        "messages": [AIMessage(content=result.get("content", ""))],
        "restaurants": restaurants,  # ✅ Stored in state
        "selected_restaurant": selected_restaurant,  # ✅ Stored in state
        "next_agent": result.get("handoff_to"),
        "current_agent": "restaurant_finder",
        "context": {**(state.get("context") or {}), **(result.get("context") or {})},
        "final_response": result.get("content")
    }
```

---

### 4. Booking Agent Node (restaurant_workflow.py)

```python
def _booking_agent_node(self, state: RestaurantBookingState) -> Dict[str, Any]:
    """
    Execute booking - extracts restaurant from CONVERSATION HISTORY.
    """
    user_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break
    
    correlation_id = state["correlation_id"]
    context = state.get("context", {})
    
    # ✅ Extract restaurant from conversation history using LLM
    conversation_history = context.get("conversation_history", "")
    
    if conversation_history:
        # ✅ Use LLM to extract restaurant details from conversation
        from src.core import AmazonNovaProvider
        bedrock = AmazonNovaProvider("amazon.nova-lite-v1:0")
        
        extract_prompt = f"""Extract restaurant booking details from conversation.

Conversation History:
{conversation_history}

Current Message: {user_message}

Extract:
1. Restaurant name (if mentioned)
2. Restaurant ID (if mentioned)
3. City/Location

Return JSON:
{{"restaurant_name": "...", "restaurant_id": "...", "city": "..."}}
"""
        
        try:
            extraction = bedrock.invoke(
                messages=[{"role": "user", "content": [{"text": extract_prompt}]}],
                temperature=0.0,
                max_tokens=200
            )
            
            import json
            extracted = json.loads(extraction["content"])
            
            # ✅ If restaurant mentioned, search for it
            if extracted.get("restaurant_name") or extracted.get("city"):
                # Call MCP tool to search
                search_result = self.mcp_tools["fetchRestaurantDetails"].invoke({
                    "city": extracted.get("city", ""),
                    "restaurantName": extracted.get("restaurant_name", ""),
                    "requestId": f"{correlation_id}_extract_restaurant"
                })
                
                if search_result.get("restaurants"):
                    context["restaurants"] = search_result["restaurants"]
        
        except Exception as e:
            print(f"[DEBUG] Restaurant extraction error: {e}")
    
    # ✅ Add partial params from memory
    if state.get("partial_booking_params"):
        context["partial_params"] = state["partial_booking_params"]
    
    # ✅ Build full conversation history
    memory_history = context.get("conversation_history", "")
    session_turns = []
    for msg in state.get("messages", []):
        if isinstance(msg, HumanMessage):
            session_turns.append(f"USER: {msg.content}")
        elif isinstance(msg, AIMessage):
            session_turns.append(f"ASSISTANT: {msg.content}")
    context["conversation_history"] = f"{memory_history}\n{''.join(session_turns)}".strip()
    
    # ✅ Call booking agent
    result = self.booking_agent.process(user_message, correlation_id, context)
    
    # Handle missing fields, HITL, success/error...
    # (same as before)
```

---

### 5. Memory Storage (restaurant_workflow.py)

```python
def _store_memory(self, user_id: str, session_id: str, 
                  user_message: str, assistant_response: str,
                  intent: str, metadata: Dict[str, Any]):
    """
    Store conversation + restaurant context in AgentCore Memory.
    """
    if not self.memory_id or not assistant_response:
        return
    
    try:
        import datetime, base64, json
        
        # ✅ Build metadata with ALL context
        memory_metadata = {
            'intent': {'stringValue': intent or 'unknown'}
        }
        
        # ✅ Store restaurant search results (if any)
        if metadata.get('restaurants'):
            restaurants_json = json.dumps(metadata['restaurants'])
            restaurants_b64 = base64.b64encode(restaurants_json.encode()).decode()
            memory_metadata['restaurants_b64'] = {'stringValue': restaurants_b64}
        
        # ✅ Store selected restaurant (if any)
        if metadata.get('selected_restaurant'):
            selected_json = json.dumps(metadata['selected_restaurant'])
            selected_b64 = base64.b64encode(selected_json.encode()).decode()
            memory_metadata['selected_restaurant_b64'] = {'stringValue': selected_b64}
        
        # ✅ Store booking params (if booking completed)
        if metadata.get('booking_id'):
            memory_metadata['booking_id'] = {'stringValue': metadata['booking_id']}
            memory_metadata['booking_completed'] = {'stringValue': 'true'}
            
            if metadata.get('partial_booking_params'):
                params_json = json.dumps(metadata['partial_booking_params'])
                params_b64 = base64.b64encode(params_json.encode()).decode()
                memory_metadata['booking_params_b64'] = {'stringValue': params_b64}
        
        # ✅ Create event in AgentCore Memory
        self.memory_client.create_event(
            memoryId=self.memory_id,
            actorId=user_id,
            sessionId=session_id,
            eventTimestamp=datetime.datetime.utcnow().isoformat() + 'Z',
            payload=[
                {'conversational': {'content': {'text': user_message}, 'role': 'USER'}},
                {'conversational': {'content': {'text': assistant_response}, 'role': 'ASSISTANT'}}
            ],
            metadata=memory_metadata
        )
    except Exception as e:
        print(f"Memory storage error: {e}")
```

---

### 6. Memory Retrieval (restaurant_workflow.py)

```python
def _retrieve_memory(self, user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Retrieve ALL context from AgentCore Memory:
    - Conversation history
    - Restaurant search results
    - Selected restaurant
    - Partial booking params
    - Booking completion status
    """
    if not self.memory_id:
        return {
            'conversation_history': '',
            'restaurants': [],
            'selected_restaurant': None,
            'booking_params': {},
            'booking_completed': False
        }
    
    try:
        response = self.memory_client.list_events(
            memoryId=self.memory_id,
            actorId=user_id,
            sessionId=session_id,
            maxResults=10
        )
        
        import json, base64
        events = response.get('events', [])
        
        # ✅ Extract all context from memory
        restaurants = []
        selected_restaurant = None
        booking_params = {}
        booking_completed = False
        
        for event in reversed(events):
            metadata = event.get('metadata', {})
            
            # ✅ Extract restaurants
            if 'restaurants_b64' in metadata and not restaurants:
                try:
                    rest_b64 = metadata['restaurants_b64'].get('stringValue', '')
                    restaurants = json.loads(base64.b64decode(rest_b64).decode())
                except: pass
            
            # ✅ Extract selected restaurant
            if 'selected_restaurant_b64' in metadata and not selected_restaurant:
                try:
                    sel_b64 = metadata['selected_restaurant_b64'].get('stringValue', '')
                    selected_restaurant = json.loads(base64.b64decode(sel_b64).decode())
                except: pass
            
            # ✅ Extract booking params
            if 'booking_params_b64' in metadata:
                try:
                    params_b64 = metadata['booking_params_b64'].get('stringValue', '')
                    booking_params = json.loads(base64.b64decode(params_b64).decode())
                except: pass
            
            # ✅ Check booking completion
            if 'booking_completed' in metadata:
                booking_completed = metadata['booking_completed'].get('stringValue') == 'true'
            
            if booking_completed:
                break
        
        # ✅ Build conversation history
        conversation_turns = []
        for event in events:
            for item in event.get('payload', []):
                if 'conversational' in item:
                    role = item['conversational']['role']
                    text = item['conversational']['content']['text']
                    conversation_turns.append(f"{role}: {text}")
        
        conversation_history = "\n".join(conversation_turns)
        
        return {
            'conversation_history': conversation_history,
            'restaurants': restaurants,
            'selected_restaurant': selected_restaurant,
            'booking_params': booking_params,
            'booking_completed': booking_completed
        }
    
    except Exception as e:
        print(f"Memory retrieval error: {e}")
        return {
            'conversation_history': '',
            'restaurants': [],
            'selected_restaurant': None,
            'booking_params': {},
            'booking_completed': False
        }
```

---

## Benefits of Corrected Approach

### ✅ Stateless Backend
- Backend doesn't depend on UI maintaining state
- Works with any client (web, mobile, voice, SMS, API)

### ✅ Single Source of Truth
- AgentCore Memory is the ONLY state store
- No inconsistency between UI session and backend memory

### ✅ Scalable
- Can switch UI frameworks without changing backend
- Can add new channels (Alexa, WhatsApp) without code changes

### ✅ LLM-Powered Context Extraction
- LLM extracts restaurant details from conversation
- More natural and flexible than explicit parameters

### ✅ Simpler API Contract
```python
# ✅ Clean API
POST /invoke
{
  "inputText": "Book the Italian place for tomorrow",
  "userId": "user123",
  "sessionId": "session456"
}

# ❌ Messy API (current)
POST /invoke
{
  "inputText": "Book the Italian place for tomorrow",
  "userId": "user123",
  "sessionId": "session456",
  "restaurants": [...],  # UI state leaking
  "selectedRestaurant": {...}  # UI state leaking
}
```

---

## Summary

**Your understanding is 100% correct:**

1. ✅ Orchestrator should ONLY extract `user_id`, `session_id`, `user_message`
2. ✅ All context retrieved from AgentCore Memory
3. ✅ LLM extracts restaurant details from conversation history
4. ✅ Backend is stateless and UI-agnostic

**Current implementation has design flaw:**
- Passing `restaurants` and `selected_restaurant` from payload
- Creates tight coupling between UI and backend
- Violates stateless principle

**Recommendation:**
Remove `restaurants` and `selected_restaurant` parameters from orchestrator and workflow, store/retrieve everything from AgentCore Memory.
