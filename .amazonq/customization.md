# Amazon Q Customization Instructions
# Reference: application-prod.md for complete production patterns

## When Generating Agent Code

### Always Include These Imports
```python
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from strands_agents import StrandsAgent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from aws_xray_sdk.core import xray_recorder
import structlog
import uuid
```

### State Schema Template
Use this exact structure for RestaurantBookingState:
```python
class RestaurantBookingState(TypedDict):
    correlation_id: str
    user_id: str
    session_id: str
    messages: Annotated[List[AnyMessage], add_messages]
    intent: str
    next: str
    # Add domain-specific fields as needed
```

### Agent Node Template
```python
def {agent_name}_node(state: RestaurantBookingState) -> dict:
    """
    {Agent description}
    
    Follows Single Responsibility Principle.
    Uses circuit breaker for LLM fallback.
    """
    # Get LLM with fallback
    llm_provider = get_llm_provider_with_fallback()
    
    # Create Strands agent
    agent = StrandsAgent(
        llm_provider=llm_provider,
        tools=[...],
        system_prompt=load_prompt("{agent_name}", PROMPT_VERSION),
        temperature=0.3
    )
    
    # Invoke with error handling
    try:
        result = agent.invoke(state)
        return result
    except Exception as e:
        logger.error("agent_error", agent="{agent_name}", error=str(e))
        raise
```

### Tool Invocation Template
```python
# Always include requestId for idempotency
result = {tool_name}.invoke({
    # Required parameters
    "param1": value1,
    "param2": value2,
    # Idempotency key (REQUIRED)
    "requestId": f"{state['correlation_id']}_{operation}_{attempt}"
})
```

### SAGA Pattern Template
```python
def operation_with_saga(state: RestaurantBookingState) -> dict:
    """Operation with SAGA compensation"""
    compensation_stack = []
    
    try:
        # Step 1: Compensatable operation
        result1 = step1_operation(state)
        compensation_stack.append(("compensate_step1", result1["id"]))
        
        # Step 2: Compensatable operation
        result2 = step2_operation(state)
        compensation_stack.append(("compensate_step2", result2["id"]))
        
        return {"success": True, "result": result2}
        
    except Exception as e:
        # Rollback in reverse order
        logger.error("saga_failure", error=str(e))
        for operation, resource_id in reversed(compensation_stack):
            try:
                compensate(operation, resource_id)
                logger.info("compensated", operation=operation, resource_id=resource_id)
            except Exception as comp_error:
                logger.error("compensation_failed", error=str(comp_error))
        raise
```

### Circuit Breaker Template
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = "CLOSED"
        self.last_failure_time = None
    
    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise
```

### LLM Provider Abstraction Template
```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def invoke(self, prompt: str, **kwargs) -> str:
        pass

class AnthropicProvider(LLMProvider):
    def invoke(self, prompt: str, **kwargs) -> str:
        return anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )

class AmazonNovaProvider(LLMProvider):
    def invoke(self, prompt: str, **kwargs) -> str:
        return bedrock_client.invoke_model(
            modelId="amazon.nova-lite-v1:0",
            body=json.dumps({"prompt": prompt, **kwargs})
        )

def get_llm_provider_with_fallback() -> LLMProvider:
    """Get LLM with circuit breaker fallback"""
    circuit_breaker = CircuitBreaker()
    try:
        return circuit_breaker.call(lambda: AnthropicProvider())
    except CircuitOpenError:
        logger.warning("circuit_open_using_fallback")
        return AmazonNovaProvider()
```

### Observability Template
```python
@xray_recorder.capture('operation_name')
def operation(state: RestaurantBookingState) -> dict:
    """Operation with full observability"""
    correlation_id = state["correlation_id"]
    logger = structlog.get_logger().bind(correlation_id=correlation_id)
    
    logger.info("operation_started", user_id=state["user_id"])
    
    try:
        # Operation logic
        result = perform_operation(state)
        
        logger.info("operation_completed", duration_ms=123)
        return result
        
    except Exception as e:
        logger.error("operation_failed", error=str(e))
        raise
```

## Code Quality Checklist
When generating code, ensure:
- [ ] Correlation ID propagated through all operations
- [ ] RequestId included in all tool calls
- [ ] Circuit breaker implemented for LLM calls
- [ ] SAGA compensation for multi-step operations
- [ ] Input validation for prompt injection
- [ ] Structured logging with context
- [ ] X-Ray tracing decorators
- [ ] Cost tracking for model invocations
- [ ] Type hints for all functions
- [ ] Docstrings for all public functions

## Example: Complete Agent Implementation
See `application-prod.md` sections:
- "Production Architecture: 5-Layer Design" for full patterns
- "Layer 3: Agent Execution (Strands)" for agent examples
- "Security & Governance" for validation patterns
- "Cost Optimization Strategies" for model selection
