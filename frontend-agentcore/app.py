import streamlit as st
import json
import uuid
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import boto3

# Get deployed runtime ARN
AGENT_RUNTIME_ARN = os.getenv("AGENT_RUNTIME_ARN")
if not AGENT_RUNTIME_ARN:
    st.error("❌ AGENT_RUNTIME_ARN not found in .env file")
    st.stop()

# Extract runtime ID from ARN
RUNTIME_ID = AGENT_RUNTIME_ARN.split('/')[-1]

# Initialize Bedrock AgentCore client
bedrock_agentcore = boto3.client('bedrock-agentcore')

st.set_page_config(page_title="Restaurant Booking", page_icon="🍽️", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{uuid.uuid4().hex}"  # 33+ chars
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
# Removed: restaurants and selected_restaurant - backend manages via AgentCore Memory

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
        st.session_state.session_id = f"session_{uuid.uuid4().hex}"
        st.rerun()
    
    st.markdown("---")
    st.text(f"Session: {st.session_state.session_id[:8]}...")
    
    st.session_state.debug_mode = st.checkbox("🐛 Debug Mode", value=st.session_state.debug_mode)
    
    if st.button("🔄 New Session", use_container_width=True, help="Clear conversation and start fresh"):
        st.session_state.messages = []
        st.session_state.session_id = f"session_{uuid.uuid4().hex}"
        st.success("New session started!")
        st.rerun()

st.title("🍽️ Restaurant Booking Assistant")

if not st.session_state.user_id or not st.session_state.get('phone'):
    st.warning("⚠️ Please enter your User ID and Phone Number in the sidebar to start.")
    st.stop()

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
                # Invoke deployed AgentCore Runtime (stateless - no restaurant state)
                response = bedrock_agentcore.invoke_agent_runtime(
                    agentRuntimeArn=AGENT_RUNTIME_ARN,
                    runtimeSessionId=st.session_state.session_id,
                    runtimeUserId=st.session_state.user_id,
                    payload=json.dumps({
                        "inputText": enhanced_prompt,
                        "userId": st.session_state.user_id
                    }).encode('utf-8')
                )
                
                # Parse response - handle StreamingBody or direct string
                raw_response = response.get('response') or response.get('body')
                if hasattr(raw_response, 'read'):
                    raw_response = raw_response.read().decode('utf-8')
                if isinstance(raw_response, (bytes, bytearray)):
                    raw_response = raw_response.decode('utf-8')
                try:
                    response_data = json.loads(raw_response or '{}')
                    assistant_message = response_data.get('response', raw_response)
                    # Backend manages all state via AgentCore Memory
                except (json.JSONDecodeError, TypeError):
                    assistant_message = str(raw_response)
                
                # Debug info
                if st.session_state.debug_mode:
                    with st.expander("🐛 Debug Info", expanded=False):
                        st.json({
                            "runtime_id": RUNTIME_ID,
                            "session_id": st.session_state.session_id,
                            "user_id": st.session_state.user_id,
                            "response": response
                        })
                
                # Remove restaurant IDs from display
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
