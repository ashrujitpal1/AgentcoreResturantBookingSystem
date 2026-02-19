import streamlit as st
import json
import uuid
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools

st.set_page_config(page_title="Restaurant Booking", page_icon="🍽️", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"req_{uuid.uuid4()}"
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "restaurants" not in st.session_state:
    st.session_state.restaurants = []
if "selected_restaurant" not in st.session_state:
    st.session_state.selected_restaurant = None
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
if "is_first_message" not in st.session_state:
    st.session_state.is_first_message = True

with st.sidebar:
    st.title("🍽️ Restaurant Booking")
    st.markdown("---")
    
    user_id_input = st.text_input(
        "User ID (Actor ID)",
        value=st.session_state.user_id,
        placeholder="e.g., user_123"
    )
    
    phone_input = st.text_input(
        "Phone Number",
        value=st.session_state.get('phone', ''),
        placeholder="e.g., 5551234567",
        help="10+ digits required for bookings"
    )
    
    if user_id_input != st.session_state.user_id or phone_input != st.session_state.get('phone', ''):
        st.session_state.user_id = user_id_input
        st.session_state.phone = phone_input
        st.session_state.messages = []
        st.session_state.restaurants = []
        st.session_state.selected_restaurant = None
        st.session_state.session_id = f"req_{uuid.uuid4()}"
        st.session_state.is_first_message = True
        st.rerun()
    
    st.markdown("---")
    st.text(f"Session: {st.session_state.session_id[:8]}...")
    
    st.session_state.debug_mode = st.checkbox("🐛 Debug Mode", value=st.session_state.debug_mode)
    
    if st.button("🔄 New Session", use_container_width=True, help="Clear conversation and start fresh"):
        st.session_state.messages = []
        st.session_state.restaurants = []
        st.session_state.selected_restaurant = None
        st.session_state.session_id = f"req_{uuid.uuid4()}"
        st.session_state.is_first_message = True
        st.success("New session started!")
        st.rerun()

st.title("🍽️ Restaurant Booking Assistant")

if not st.session_state.user_id or not st.session_state.get('phone'):
    st.warning("⚠️ Please enter your User ID and Phone Number in the sidebar to start.")
    st.stop()

# Show greeting on first load
if st.session_state.is_first_message and st.session_state.user_id:
    with st.chat_message("assistant"):
        with st.spinner("Loading your preferences..."):
            try:
                if 'workflow' not in st.session_state:
                    st.session_state.workflow = RestaurantBookingWorkflow(get_mcp_tools())
                
                greeting_result = st.session_state.workflow.invoke(
                    user_message="",
                    user_id=st.session_state.user_id,
                    session_id=st.session_state.session_id,
                    phone=st.session_state.get('phone'),
                    is_first_message=True
                )
                
                greeting_msg = greeting_result.get('final_response', '👋 Welcome!')
                st.markdown(greeting_msg)
                st.session_state.messages.append({"role": "assistant", "content": greeting_msg})
                st.session_state.is_first_message = False
            except Exception as e:
                st.error(f"Error loading preferences: {e}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about restaurants or make a booking..."):
    # Inject phone number into message if booking intent detected
    enhanced_prompt = prompt
    if any(word in prompt.lower() for word in ['book', 'reserve', 'reservation', 'table']):
        if st.session_state.get('phone'):
            enhanced_prompt = f"{prompt}\nPhone: {st.session_state.phone}"
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if 'workflow' not in st.session_state:
                    st.session_state.workflow = RestaurantBookingWorkflow(get_mcp_tools())
                
                result = st.session_state.workflow.invoke(
                    user_message=enhanced_prompt,
                    user_id=st.session_state.user_id,
                    session_id=st.session_state.session_id,
                    restaurants=st.session_state.restaurants,
                    selected_restaurant=st.session_state.selected_restaurant,
                    phone=st.session_state.get('phone'),
                    is_first_message=False
                )
                
                # Debug info
                if st.session_state.debug_mode:
                    with st.expander("🐛 Debug Info", expanded=False):
                        st.json({
                            "intent": result.get('intent'),
                            "current_agent": result.get('current_agent'),
                            "restaurants_count": len(st.session_state.restaurants),
                            "selected_restaurant": st.session_state.selected_restaurant.get('name') if st.session_state.selected_restaurant else None,
                            "partial_booking_params": result.get('partial_booking_params'),
                            "booking_id": result.get('booking_id')
                        })
                
                # Handle restaurant selection logic
                if result.get('restaurants'):
                    restaurants = result['restaurants']
                    # REPLACE restaurants, don't accumulate
                    st.session_state.restaurants = restaurants
                    
                    # Auto-select if single restaurant
                    if len(restaurants) == 1:
                        st.session_state.selected_restaurant = restaurants[0]
                    # Multiple restaurants - check if user confirmed one
                    elif result.get('selected_restaurant'):
                        st.session_state.selected_restaurant = result['selected_restaurant']
                    else:
                        # Clear selection when new search results arrive
                        st.session_state.selected_restaurant = None
                
                assistant_message = result.get('final_response', 'Request processed successfully.')
                
                # Remove restaurant IDs from display (keep internal data intact)
                import re
                display_message = re.sub(r'\s*ID:\s*[\w_-]+', '', assistant_message)
                display_message = re.sub(r'\s*\(ID:[^)]+\)', '', display_message)
                
                st.markdown(display_message)
                st.session_state.messages.append({"role": "assistant", "content": display_message})
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

st.markdown("---")
st.caption("Powered by Amazon Bedrock AgentCore")
