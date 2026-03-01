"""
Orchestrator entrypoint for AgentCore Runtime.
Uses LangGraph workflow with Strands agents and MCP Gateway integration.
"""
import os
import sys
import logging
from opentelemetry import trace

# Add project root to path
sys.path.insert(0, '/var/task')

from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from src.workflows.restaurant_workflow import RestaurantBookingWorkflow
from src.tools.mcp_gateway_client import get_mcp_client

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = BedrockAgentCoreApp()


@app.entrypoint
def handler(payload: dict, context: RequestContext) -> dict:
    """
    Main entrypoint for AgentCore Runtime.
    Uses LangGraph workflow orchestrating Strands agents with MCP tools.
    """
    user_message = payload.get("inputText", "")
    user_id = payload.get("userId", "unknown")
    # session_id comes from the SDK header via RequestContext, fallback to payload
    session_id = (context.session_id if context and context.session_id
                  else payload.get("sessionId") or f"session_{os.urandom(8).hex()}")
    trace_id = payload.get("traceId")
    # Removed: restaurants and selected_restaurant - all context from AgentCore Memory

    # Propagate traceId into current span if provided
    if trace_id:
        span = trace.get_current_span()
        if span and span.is_recording():
            span.set_attribute("bedrock.agentcore.trace_id", trace_id)

    logger.info(f"[ORCHESTRATOR] Invoked with message: {user_message[:100]}")
    logger.info(f"[ORCHESTRATOR] User ID: {user_id}, Session ID: {session_id}")

    try:
        logger.info(f"[ORCHESTRATOR] Getting MCP client...")
        mcp_client = get_mcp_client()

        logger.info(f"[ORCHESTRATOR] Starting MCP client session...")
        with mcp_client:
            mcp_tools = mcp_client.list_tools_sync()
            logger.info(f"[ORCHESTRATOR] Loaded {len(mcp_tools)} MCP tools from Gateway")

            for tool in mcp_tools:
                logger.info(f"[ORCHESTRATOR] Tool available: {tool.tool_name}")

            workflow = RestaurantBookingWorkflow(mcp_tools)

            logger.info(f"[ORCHESTRATOR] Invoking workflow...")
            result = workflow.invoke(
                user_message=user_message,
                user_id=user_id,
                session_id=session_id,
                is_first_message=False
            )

            response_text = result.get("final_response", "I couldn't process your request.")

            logger.info(f"[ORCHESTRATOR] Workflow completed. Intent: {result.get('intent')}")

            return {
                "response": response_text,
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "intent": result.get("intent"),
                    "booking_id": result.get("booking_id")
                }
            }

    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Workflow failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "response": "I encountered an error processing your request. Please try again.",
            "error": str(e)
        }
