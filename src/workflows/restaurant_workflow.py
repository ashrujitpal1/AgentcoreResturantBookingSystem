"""
LangGraph Workflow - Orchestrates Strands agents with conditional routing.
Implements SAGA pattern for transaction safety.
Integrates AgentCore Memory for conversation persistence.
"""
import uuid
import os
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import boto3

from .state import RestaurantBookingState
from src.agents import IntentClassifierAgent, RestaurantFinderAgent, BookingAgent


class RestaurantBookingWorkflow:
    """
    LangGraph workflow orchestrating Strands agents.
    Implements handoff pattern, SAGA compensation, and AgentCore Memory.
    """
    
    def __init__(self, mcp_tools: Dict[str, Any]):
        self.mcp_tools = mcp_tools
        
        # Initialize agents
        self.intent_classifier = IntentClassifierAgent()
        self.restaurant_finder = RestaurantFinderAgent(mcp_tools)
        self.booking_agent = BookingAgent(mcp_tools)
        
        # Initialize AgentCore Memory client
        self.memory_client = boto3.client('bedrock-agentcore')
        self.memory_id = os.getenv('MEMORY_ID')
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with conditional routing"""
        workflow = StateGraph(RestaurantBookingState)
        
        # Add nodes (plain Python functions wrapping Strands agents)
        workflow.add_node("entry_router", self._entry_router_node)
        workflow.add_node("restaurant_finder", self._restaurant_finder_node)
        workflow.add_node("booking_agent", self._booking_agent_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Set entry point
        workflow.set_entry_point("entry_router")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "entry_router",
            self._route_by_intent,
            {
                "search": "restaurant_finder",
                "booking": "booking_agent",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "restaurant_finder",
            self._route_after_search,
            {
                "booking": "booking_agent",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "booking_agent",
            self._route_after_booking,
            {
                "error": "error_handler",
                "end": END
            }
        )
        
        workflow.add_edge("error_handler", END)
        
        return workflow
    
    # ========== NODE FUNCTIONS (wrap Strands agents) ==========
    
    def _entry_router_node(self, state: RestaurantBookingState) -> Dict[str, Any]:
        """Entry point: Classify intent using IntentClassifierAgent"""
        user_message = state["messages"][-1].content
        correlation_id = state["correlation_id"]
        
        print(f"[DEBUG] Entry Router - User message: {user_message}")
        print(f"[DEBUG] Entry Router - Existing context: {state.get('context')}")
        
        # Call Strands agent with context (includes last_response from memory)
        result = self.intent_classifier.process(user_message, correlation_id, state.get('context'))
        
        # Preserve existing context (e.g., selected_restaurant)
        existing_context = state.get("context") or {}
        new_context = result.get("extracted_entities", {})
        merged_context = {**existing_context, **new_context}
        
        print(f"[DEBUG] Entry Router - Intent: {result.get('intent')}, Merged context: {merged_context}")
        
        return {
            "intent": result.get("intent"),
            "confidence": result.get("confidence"),
            "current_agent": "intent_classifier",
            "context": merged_context
        }
    
    def _restaurant_finder_node(self, state: RestaurantBookingState) -> Dict[str, Any]:
        """Search restaurants using RestaurantFinderAgent"""
        user_message = state["messages"][-1].content
        correlation_id = state["correlation_id"]
        context = state.get("context")
        
        # Call Strands agent
        result = self.restaurant_finder.process(user_message, correlation_id, context)
        
        restaurants = result.get("restaurants", [])
        
        # Check if user is selecting from multiple restaurants
        selected_restaurant = None
        if len(state.get("restaurants", [])) > 1:
            # User might be confirming a restaurant by name
            for r in state["restaurants"]:
                if r.get('name', '').lower() in user_message.lower():
                    selected_restaurant = r
                    break
        
        # Add AI response to messages
        ai_message = AIMessage(content=result.get("content", ""))
        
        return {
            "messages": [ai_message],
            "restaurants": restaurants,  # ALWAYS use new search results, never fallback to state
            "selected_restaurant": selected_restaurant,
            "next_agent": result.get("handoff_to"),
            "current_agent": "restaurant_finder",
            "context": result.get("context"),
            "final_response": result.get("content", "I couldn't find any restaurants matching your criteria.")
        }
    
    def _booking_agent_node(self, state: RestaurantBookingState) -> Dict[str, Any]:
        """Execute booking with SAGA pattern using BookingAgent"""
        user_message = state["messages"][-1].content
        correlation_id = state["correlation_id"]
        context = state.get("context", {})
        
        print(f"[DEBUG] Booking Agent - User message: {user_message}")
        print(f"[DEBUG] Booking Agent - Context: {context}")
        print(f"[DEBUG] Booking Agent - State restaurants: {state.get('restaurants')}")
        print(f"[DEBUG] Booking Agent - Partial params: {state.get('partial_booking_params')}")
        
        # Use selected restaurant or restaurants from state
        if context.get("selected_restaurant"):
            context["restaurants"] = [context["selected_restaurant"]]
            print(f"[DEBUG] Booking Agent - Using selected_restaurant: {context['selected_restaurant'].get('name')}")
        elif state.get("restaurants"):
            # Extract restaurant name from conversation history if available
            if context.get("conversation_history") and len(state["restaurants"]) > 1:
                # Use LLM to identify which restaurant from conversation
                from src.core import AmazonNovaProvider
                bedrock = AmazonNovaProvider("amazon.nova-lite-v1:0", region=os.getenv('AWS_REGION', 'us-east-1'))
                restaurant_list = "\n".join([f"{r.get('name')} (ID: {r.get('restaurantId')})" for r in state["restaurants"]])
                match_prompt = f"""Which restaurant ID?

Conversation:
{context['conversation_history']}

User: {user_message}

Restaurants:
{restaurant_list}

Return ONLY the restaurant ID (e.g., rest_001). No explanation.

If user names a restaurant → return its ID
If user says "yes"/"ok"/"book it" → return last mentioned restaurant ID
If unclear → return FIRST restaurant ID

ID:"""
                
                try:
                    match_response = bedrock.invoke(
                        messages=[{"role": "user", "content": [{"text": match_prompt}]}],
                        temperature=0.0,
                        max_tokens=50
                    )
                    matched_id = match_response["content"].strip()
                    for rest in state["restaurants"]:
                        if rest.get("restaurantId") == matched_id:
                            context["restaurants"] = [rest]
                            print(f"[DEBUG] Booking Agent - LLM matched restaurant: {rest.get('name')} ({matched_id})")
                            break
                    else:
                        context["restaurants"] = state["restaurants"]
                        print(f"[DEBUG] Booking Agent - LLM match failed, using all restaurants")
                except Exception as e:
                    print(f"[DEBUG] Booking Agent - LLM matching error: {e}")
                    context["restaurants"] = state["restaurants"]
            else:
                context["restaurants"] = state["restaurants"]
            print(f"[DEBUG] Booking Agent - Using state restaurants: {len(context['restaurants'])} found")
        
        # Add accumulated partial params from state (loaded from memory)
        if state.get("partial_booking_params"):
            context["partial_params"] = state["partial_booking_params"]
        
        # Add conversation history from messages for context
        if len(state.get("messages", [])) > 1:
            prev_messages = [msg.content for msg in state["messages"][:-1]]
            context["memory_context"] = " ".join(prev_messages[-3:])  # Last 3 turns
        
        print(f"[DEBUG] Booking Agent - Final context passed to agent: {context}")
        
        # Call Strands agent (SAGA workflow inside)
        result = self.booking_agent.process(user_message, correlation_id, context)
        
        print(f"[DEBUG] Booking Agent - Result: {result}")
        
        # Handle missing fields - ask user for more info
        if result.get("missing_fields"):
            # Merge new partial params with existing ones
            accumulated_params = state.get("partial_booking_params") or {}
            new_params = result.get("partial_params", {})
            for key, value in new_params.items():
                if value:  # Only update if value is not None/empty
                    accumulated_params[key] = value
            
            return {
                "current_agent": "booking_agent",
                "final_response": result.get("content"),
                "partial_booking_params": accumulated_params
            }
        
        if result.get("hitl_required"):
            return {
                "hitl_required": True,
                "hitl_reason": result.get("reason"),
                "booking_params": result.get("booking_params"),
                "current_agent": "booking_agent",
                "final_response": f"⚠️ Approval Required: {result.get('reason')}"
            }
        
        if result.get("success"):
            ai_message = AIMessage(content=result.get("content"))
            return {
                "messages": [ai_message],
                "booking_id": result.get("booking_details", {}).get("booking_id"),
                "token_amount": result.get("booking_details", {}).get("token_amount"),
                "compensation_stack": result.get("compensation_log", []),
                "current_agent": "booking_agent",
                "final_response": result.get("content")
            }
        else:
            return {
                "error": result.get("error"),
                "compensation_stack": result.get("compensation_log", []),
                "current_agent": "booking_agent",
                "final_response": result.get("content")
            }
    
    def _error_handler_node(self, state: RestaurantBookingState) -> Dict[str, Any]:
        """Handle errors with graceful degradation"""
        error = state.get("error", "Unknown error")
        compensation_log = state.get("compensation_stack", [])
        
        error_message = f"""❌ An error occurred: {error}

Rollback actions taken:
{chr(10).join(compensation_log) if compensation_log else 'None'}

Please try again or contact support."""
        
        ai_message = AIMessage(content=error_message)
        
        return {
            "messages": [ai_message],
            "final_response": error_message
        }
    
    # ========== ROUTING FUNCTIONS ==========
    
    def _route_by_intent(self, state: RestaurantBookingState) -> Literal["search", "booking", "error"]:
        """Route based on classified intent"""
        intent = state.get("intent")
        
        if state.get("error"):
            return "error"
        
        if intent == "search":
            return "search"
        elif intent in ["booking", "payment"]:
            return "booking"
        else:
            return "search"  # Default fallback
    
    def _route_after_search(self, state: RestaurantBookingState) -> Literal["booking", "end"]:
        """Route after restaurant search - check for handoff"""
        next_agent = state.get("next_agent")
        
        if next_agent == "booking_agent":
            return "booking"
        else:
            return "end"
    
    def _route_after_booking(self, state: RestaurantBookingState) -> Literal["error", "end"]:
        """Route after booking - check for errors"""
        if state.get("error"):
            return "error"
        else:
            return "end"
    
    # ========== PUBLIC API ==========
    
    def invoke(self, user_message: str, user_id: str, session_id: str, restaurants: list = None, selected_restaurant: dict = None) -> Dict[str, Any]:
        """
        Invoke workflow with user message.
        Retrieves conversation history from AgentCore Memory.
        
        Args:
            user_message: User's input message
            user_id: User identifier (actorId)
            session_id: Session identifier (used as correlation_id for tracing)
            restaurants: Restaurant list from previous search (from Streamlit session)
            selected_restaurant: Selected restaurant (from Streamlit session)
        
        Returns:
            Final state with response
        """
        # Retrieve booking state AND conversation history from AgentCore Memory
        memory_data = self._retrieve_memory(user_id, session_id)
        memory_params = memory_data.get('booking_params', {})
        conversation_history = memory_data.get('conversation_history', '')
        
        print(f"[DEBUG] Memory params: {memory_params}")
        print(f"[DEBUG] Conversation history: {conversation_history[:200] if conversation_history else 'None'}...")
        
        # Initialize state with memory data as fallback
        initial_state = RestaurantBookingState(
            correlation_id=session_id,
            user_id=user_id,
            session_id=session_id,
            messages=[HumanMessage(content=user_message)],
            intent=None,
            confidence=None,
            restaurants=restaurants or [],
            selected_restaurant_id=selected_restaurant.get('restaurantId') if selected_restaurant else None,
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
            context={
                'selected_restaurant': selected_restaurant,
                'conversation_history': conversation_history
            } if (selected_restaurant or conversation_history) else {},
            final_response=None
        )
        
        # Execute workflow
        final_state = self.app.invoke(initial_state)
        
        # Store conversation in AgentCore Memory
        self._store_memory(
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            assistant_response=final_state.get("final_response", ""),
            intent=final_state.get("intent"),
            metadata=final_state
        )
        
        return final_state
    
    def _retrieve_memory(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Retrieve booking state AND full conversation history from AgentCore Memory"""
        if not self.memory_id:
            return {'booking_params': {}, 'conversation_history': ''}
        
        try:
            response = self.memory_client.list_events(
                memoryId=self.memory_id,
                actorId=user_id,
                sessionId=session_id,
                maxResults=10
            )
            
            import json
            import base64
            events = response.get('events', [])
            
            print(f"[DEBUG] Retrieved {len(events)} events for session {session_id[:20]}...")
            
            # Extract booking params
            booking_params = {}
            for event in reversed(events):
                if 'booking_params_b64' in event.get('metadata', {}):
                    try:
                        params_b64 = event['metadata']['booking_params_b64'].get('stringValue', '')
                        booking_params = json.loads(base64.b64decode(params_b64).decode())
                        break
                    except: pass
            
            # Build full conversation history from all events
            conversation_turns = []
            for event in events:
                for item in event.get('payload', []):
                    if 'conversational' in item:
                        role = item['conversational']['role']
                        text = item['conversational']['content']['text']
                        conversation_turns.append(f"{role}: {text}")
            
            conversation_history = "\n".join(conversation_turns)
            
            return {'booking_params': booking_params, 'conversation_history': conversation_history}
        except Exception as e:
            print(f"[DEBUG] Memory retrieval exception: {e}")
            return {'booking_params': {}, 'conversation_history': ''}
    
    def _store_memory(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        assistant_response: str,
        intent: str,
        metadata: Dict[str, Any]
    ):
        """Store conversation turn and booking state in AgentCore Memory"""
        if not self.memory_id or not assistant_response:
            return
        
        try:
            import datetime
            import base64
            import json
            
            # Build metadata with booking state (base64 encoded to avoid validation issues)
            memory_metadata = {'intent': {'stringValue': intent or 'unknown'}}
            
            # Only store booking params when booking SUCCEEDS
            if metadata.get('booking_id'):  # Booking completed successfully
                memory_metadata['booking_id'] = {'stringValue': metadata['booking_id']}
                # Store final booking params only on success
                if metadata.get('partial_booking_params'):
                    params_json = json.dumps(metadata['partial_booking_params'])
                    params_b64 = base64.b64encode(params_json.encode()).decode()
                    memory_metadata['booking_params_b64'] = {'stringValue': params_b64}
            
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
