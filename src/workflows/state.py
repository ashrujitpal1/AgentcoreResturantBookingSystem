"""
LangGraph State Schema for Restaurant Booking Workflow.
Defines all state fields with proper typing.
"""
from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class RestaurantBookingState(TypedDict):
    """
    State schema for restaurant booking workflow.
    All nodes read/write to this shared state.
    """
    # Identifiers
    correlation_id: str
    user_id: str
    session_id: str
    
    # Messages (with reducer for appending)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Intent classification
    intent: Optional[str]  # "search" | "booking" | "history" | "payment"
    confidence: Optional[float]
    
    # Restaurant search results
    restaurants: Optional[List[Dict[str, Any]]]
    selected_restaurant_id: Optional[str]
    
    # Booking details
    booking_params: Optional[Dict[str, Any]]
    partial_booking_params: Optional[Dict[str, Any]]  # Accumulated params across turns
    booking_id: Optional[str]
    token_amount: Optional[float]
    
    # SAGA compensation tracking
    compensation_stack: List[tuple[str, Any]]
    
    # HITL (Human-in-the-Loop)
    hitl_required: bool
    hitl_reason: Optional[str]
    
    # Error handling
    error: Optional[str]
    retry_count: int
    
    # Handoff tracking
    current_agent: Optional[str]
    next_agent: Optional[str]
    
    # Context for agent handoff
    context: Optional[Dict[str, Any]]
    
    # Final response
    final_response: Optional[str]
