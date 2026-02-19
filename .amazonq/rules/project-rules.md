# Amazon Q Developer - Restaurant Booking System Rules
# This file guides Amazon Q when generating code for this project

## Project Context
This is a production-grade Restaurant Booking System using AWS Bedrock AgentCore with LangGraph + Strands hybrid architecture.

## Architecture Principles

### Framework Usage
- Use **Strands Agents** for individual agent implementations with encapsulation and reusability
- Use **LangGraph** for workflow orchestration, state management, and conditional routing
- Use **plain Python functions** as LangGraph nodes that wrap Strands agents
- Use **Bedrock Converse API** for direct LLM calls with cost optimization
- Use **MCP Tools** via Gateway for Lambda function invocations

### SOLID Principles (Mandatory)
- **Single Responsibility**: Each agent handles ONE task only (Restaurant Finder = search, Booking Agent = booking)
- **Open/Closed**: Create base abstractions for Agent and LLMProvider classes, extend without modifying
- **Liskov Substitution**: Use polymorphic LLMProvider (AnthropicProvider, AmazonNovaProvider) for seamless switching
- **Interface Segregation**: Create capability-based tool interfaces
- **Dependency Inversion**: Inject dependencies via constructors, depend on abstractions not implementations

### Design Patterns (Required)
- **Handoff Pattern**: Restaurant Finder → Booking Agent with context transfer
- **SAGA Pattern**: All booking operations must be compensatable with rollback logic
- **Circuit Breaker**: Primary LLM fails → fallback to secondary (Claude → Nova)
- **Idempotency**: ALL tool calls must include requestId for deduplication

## Code Generation Rules

### State Management
```python
# Always use TypedDict for state schema
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

class RestaurantBookingState(TypedDict):
    correlation_id: str
    user_id: str
    session_id: str
    messages: Annotated[List[AnyMessage], add_messages]
    intent: str  # "search" | "booking" | "history"
    # ... other fields
```

### LangGraph Workflow Structure
```python
# Always follow this pattern
from langgraph.graph import StateGraph, END

workflow = StateGraph(RestaurantBookingState)
workflow.add_node("entry_router", entry_router_node)
workflow.add_node("restaurant_finder", restaurant_finder_node)
workflow.add_node("booking_validation", booking_validation_node)
workflow.add_conditional_edges("entry_router", route_by_intent, {...})
```

### Hybrid Agent Pattern
```python
# Strands Agent implementation
class RestaurantFinderAgent(Agent):
    def __init__(self):
        super().__init__(name="restaurant_finder")
        self.model = CostOptimizedModelRouter.select_model("restaurant_search")
    
    def process(self, user_message: str, correlation_id: str) -> dict:
        # Extract parameters using Bedrock Converse
        extracted = extract_search_params(user_message, self.model, correlation_id)
        
        # Call MCP tool
        result = fetch_restaurants_tool(
            city=extracted["city"],
            cuisine=extracted["cuisine"],
            correlation_id=correlation_id
        )
        
        return {"restaurants": result.get("restaurants", [])}

# LangGraph node wrapper
def restaurant_finder_node(state: RestaurantBookingState) -> dict:
    agent = RestaurantFinderAgent()
    correlation_id = state.get("correlation_id")
    user_message = state["messages"][-1].content
    
    result = agent.process(user_message, correlation_id)
    
    return {"restaurant_results": result["restaurants"]}
```

### MCP Tool Invocation (Idempotency Required)
```python
# ALWAYS include requestId for idempotency
def fetch_restaurants_tool(city: str, cuisine: str, correlation_id: str) -> dict:
    provider = get_llm_provider()  # MCPToolProvider
    result = provider.invoke(
        "fetch-restaurant-details-target___fetchRestaurantDetails",
        {
            "city": city,
            "cuisine": cuisine,
            "requestId": f"{correlation_id}_search_1"
        }
    )
    return parse_mcp_response(result)
```

### Error Handling (SAGA Pattern)
```python
# Always implement compensation stack
compensation_stack = []
try:
    # Step 1
    result1 = operation1()
    compensation_stack.append(("undo_operation1", result1["id"]))
    
    # Step 2
    result2 = operation2()
    compensation_stack.append(("undo_operation2", result2["id"]))
except Exception as e:
    # Rollback in reverse order
    for operation, resource_id in reversed(compensation_stack):
        compensate(operation, resource_id)
    raise
```

### Cost Optimization (Mandatory)
```python
# Always select model based on task complexity
class CostOptimizedModelRouter:
    MODELS = {
        "intent_classification": "amazon.nova-micro-v1:0",  # Cheapest
        "restaurant_search": "amazon.nova-lite-v1:0",
        "booking_validation": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    }
    
    @staticmethod
    def select_model(task: str) -> str:
        return CostOptimizedModelRouter.MODELS.get(task, "amazon.nova-lite-v1:0")

# Use Bedrock Converse for LLM calls
def extract_search_params(prompt: str, model: str, correlation_id: str) -> dict:
    bedrock = get_bedrock_provider()
    return bedrock.invoke(
        model_id=model,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inference_config={"temperature": 0.3, "maxTokens": 500},
        request_id=f"{correlation_id}_extract_1"
    )
```

### Security (Non-Negotiable)
```python
# Always validate user input for prompt injection
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all)\s+instructions?",
    r"you\s+are\s+now\s+a",
    r"disregard\s+everything"
]

def validate_input(user_message: str) -> tuple[bool, str]:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, user_message, re.IGNORECASE):
            return False, "Invalid input detected"
    return True, ""

# Always wrap user input
structured_input = f"<user_input>\n{user_message}\n</user_input>"
```

### Observability (Required)
```python
# Always use correlation IDs
correlation_id = f"req_{uuid.uuid4()}"
logger = logger.bind(correlation_id=correlation_id)

# Always use X-Ray tracing
@xray_recorder.capture('operation_name')
def operation():
    pass

# Always track costs
track_cost(correlation_id, user_id, tokens_used, model_name)
```

### Prompt Versioning (Mandatory)
```python
# NEVER hardcode prompts in code
# Always load from S3 with version
PROMPT_VERSION = "1.2.0"
PROMPT_PATH = f"s3://prompts/{agent_name}/v{PROMPT_VERSION}/system_prompt.md"

# Always pin versions in production
system_prompt = load_prompt(agent_name, PROMPT_VERSION)
```

## Naming Conventions
- Strands agents: `{AgentName}Agent` (e.g., `RestaurantFinderAgent`, `BookingAgent`)
- LangGraph nodes: `{agent_name}_node` (e.g., `restaurant_finder_node`)
- Tool functions: `{action}_{resource}_tool` (e.g., `fetch_restaurants_tool`)
- State fields: snake_case (e.g., `booking_id`, `user_details`)
- Classes: PascalCase (e.g., `RestaurantBookingState`, `CircuitBreaker`)
- Constants: UPPER_SNAKE_CASE (e.g., `PROMPT_VERSION`, `MODEL_SELECTION`)

## File Structure
```
src/
├── agents/                       # Strands Agent implementations
│   ├── intent_classifier.py      # IntentClassifierAgent + node wrapper
│   ├── restaurant_finder.py      # RestaurantFinderAgent + node wrapper
│   ├── booking_agent.py          # BookingAgent + node wrapper
│   └── payment_processor.py      # PaymentProcessorAgent + node wrapper
├── workflows/                    # LangGraph workflow orchestration
│   ├── state.py                  # RestaurantBookingState TypedDict
│   └── restaurant_workflow.py    # StateGraph with conditional routing
├── tools/                        # MCP tool wrappers
│   ├── restaurant_tools.py
│   ├── booking_tools.py
│   └── user_tools.py
├── utils/
│   ├── llm_providers.py
│   ├── circuit_breaker.py
│   ├── saga_pattern.py
│   └── cost_tracker.py
└── config/
    └── models.py
```

## Testing Requirements
- Unit tests for each agent node
- Integration tests for end-to-end workflows
- Test idempotency with duplicate requestIds
- Test SAGA compensation on failures
- Test circuit breaker fallback

## Dependencies
```python
# Core frameworks
strands-agents>=1.0.0             # Strands agent framework
langgraph>=0.2.0                  # Workflow orchestration
langchain-core>=0.3.0
langchain-aws>=0.2.0

# AWS integrations
boto3>=1.34.0
aws-xray-sdk>=2.12.0
bedrock-agentcore
bedrock-agentcore-starter-toolkit

# Validation
pydantic>=2.0.0
requests>=2.31.0
```

## What NOT to Do
- ❌ Don't create "super agents" that do everything (single responsibility)
- ❌ Don't put business logic in LangGraph nodes (use Strands agents)
- ❌ Don't hardcode prompts in code (use versioned prompts)
- ❌ Don't skip requestId in MCP tool calls (idempotency)
- ❌ Don't skip error handling and SAGA compensation logic
- ❌ Don't forget correlation IDs in logging
- ❌ Don't use "latest" for prompt versions in production
- ❌ Don't skip input validation for prompt injection
- ❌ Don't add unnecessary abstraction layers (keep it simple)

## Reference Documentation
See `application-prod.md` for complete production patterns and examples.
