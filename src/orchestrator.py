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


# Guardrail validation removed - handled by individual agents as needed
# Orchestrator should not block legitimate restaurant search/booking requests


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
    
    # Guardrail validation removed - agents handle their own guardrails as needed
    
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
