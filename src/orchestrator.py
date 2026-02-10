"""
Orchestrator entrypoint for AgentCore Runtime.
Connects Strands agents + LangGraph workflow with MCP tools.
"""
import os
import sys
import boto3

# Add project root to path
sys.path.insert(0, '/var/task')

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
from src.observability import CorrelationContext, logger
from src.security import security_context


def validate_input_with_guardrail(user_message: str) -> tuple[bool, str]:
    """Validate user input using Bedrock Guardrail"""
    guardrail_id = os.getenv("GUARDRAIL_ID")
    if not guardrail_id:
        return True, ""  # No guardrail configured
    
    try:
        bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
        
        # Use a simple prompt to test if input triggers guardrail
        response = bedrock.converse(
            modelId="amazon.nova-micro-v1:0",  # Cheapest model for validation
            messages=[{"role": "user", "content": [{"text": user_message}]}],
            inferenceConfig={"maxTokens": 10, "temperature": 0.0},
            guardrailConfig={
                "guardrailIdentifier": guardrail_id,
                "guardrailVersion": "3"
            }
        )
        return True, ""  # Input passed guardrail
        
    except Exception as e:
        error_msg = str(e)
        if "GUARDRAIL" in error_msg.upper():
            return False, "I can only help with restaurant bookings. Please ask about restaurants or reservations."
        return True, ""  # Other errors, let it pass


def handler(event: dict, context: dict) -> dict:
    """
    Main entrypoint for AgentCore Runtime.
    Invoked by Bedrock AgentCore with user message.
    """
    
    # Extract inputs
    user_message = event.get("inputText", "")
    user_id = event.get("userId", "unknown")
    session_id = event.get("sessionId", "session_" + "x" * 25)
    
    # Set correlation context
    correlation_id = event.get("requestId", f"req_{context.aws_request_id}")
    CorrelationContext.set(correlation_id, user_id, session_id)
    
    logger.info("Orchestrator invoked", user_message=user_message[:100])
    
    # Security validation
    is_valid, error = security_context.validate_input(user_message)
    if not is_valid:
        logger.error("Security validation failed", error=error)
        return {
            "response": "I cannot process that request. Please rephrase your message.",
            "error": error
        }
    
    # Guardrail input validation
    guardrail_passed, guardrail_msg = validate_input_with_guardrail(user_message)
    if not guardrail_passed:
        logger.warning("Guardrail blocked input", reason=guardrail_msg)
        return {
            "response": guardrail_msg,
            "blocked_by": "guardrail"
        }
    
    try:
        # Get MCP tools
        mcp_tools = get_mcp_tools()
        
        # Create workflow
        workflow = RestaurantBookingWorkflow(mcp_tools)
        
        # Invoke workflow
        result = workflow.invoke(user_message, user_id, session_id)
        
        # Return response
        response_text = result.get("final_response") or result.get("content", "I couldn't process your request.")
        
        logger.info("Workflow completed", intent=result.get("intent"))
        
        return {
            "response": response_text,
            "metadata": {
                "intent": result.get("intent"),
                "agent": result.get("current_agent"),
                "correlation_id": correlation_id
            }
        }
        
    except Exception as e:
        logger.error("Workflow failed", error=str(e))
        return {
            "response": "I encountered an error processing your request. Please try again.",
            "error": str(e)
        }


# For local testing
if __name__ == "__main__":
    test_event = {
        "inputText": "Find Italian restaurants in Boston",
        "userId": "test_user",
        "sessionId": "test_session_" + "x" * 20
    }
    
    class MockContext:
        aws_request_id = "test_request_123"
    
    result = handler(test_event, MockContext())
    print(result)
