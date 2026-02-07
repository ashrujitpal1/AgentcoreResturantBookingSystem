# Restaurant Booking System - Implementation Plan

## Overview
Production-grade Restaurant Booking System using AWS Bedrock AgentCore with **Strands Agents** + LangGraph hybrid architecture, implementing enterprise-grade agentic AI principles and production patterns.

**Key Production Principles Applied:**
- ✅ SOLID principles for agent design
- ✅ Cost as first-class metric with intelligent model routing
- ✅ Prompt version control with S3 storage
- ✅ Idempotent tool operations with request IDs
- ✅ Circuit breakers and LLM fallbacks
- ✅ SAGA pattern for transaction compensation
- ✅ Comprehensive observability with correlation IDs
- ✅ Security and governance by design
- ✅ Handoff Pattern for multi-agent orchestration


Next Steps:

Create base architecture (LLMProvider, Agent base class)

Implement CostOptimizedModelRouter

Build Strands agents with SOLID principles

Create LangGraph workflow with SAGA pattern

Add observability and security layers

Should I proceed with Option B implementation?

## Architecture Components

### 1. Lambda Functions (COPY AS-IS from backup)
**Source**: `/Users/USER/Work/AI/AgentCore/ResturantBookingSystem_backup/src/lambda/`

**MCP Tools with Production Patterns:**

#### Restaurant Discovery Tools (Read-Only)
- `fetch_restaurant_details.py` - Search with filters, 5s timeout, ~$0.001 cost
- `fetch_restaurant_details_by_id.py` - Get specific restaurant, 3s timeout, ~$0.0005 cost

#### User Management Tools (Mutating)
- `search_user_details.py` - User lookup, READ_ONLY, 3s timeout
- `register_user.py` - User creation, MUTATING, idempotency required

#### Booking & Payment Tools (Irreversible)
- `book_a_table.py` - Table booking, HITL for >10 guests, SAGA compensation
- `payment_api.py` - Payment processing, circuit breaker, refund compensation
- `token_amount_calculation.py` - Pure business logic, deterministic

**Tool Design Principles:**
- **Idempotency**: All tools accept requestId for deduplication
- **Side-Effect Classification**: READ_ONLY | MUTATING | IRREVERSIBLE
- **Bounded Execution**: Max 30s timeout, output size limits
- **Deterministic Behavior**: Same input → same output
- **Schema-First**: Strict input/output validation

## New Implementation Components

### 2. AgentCore Memory (NEW - Following education sample pattern)
**Reference**: `agentcore-for-education/deploy_agentcore_memory.py`

**Critical Implementation Notes:**
- Use exact IAM role structure from education sample to avoid CloudWatch logging issues
- Ensure memory role has proper CloudWatch permissions: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
- Set correct trust policy for bedrock-agentcore service principal
- Configure 3-day retention for conversation history
- Implement PII scrubbing before memory storage
- Test memory operations with validation script

**Memory Strategy:**
- **Short-term**: Last 5 conversation turns, Redis cache
- **Long-term**: User preferences, booking history, Vector DB
- **PII Protection**: Scrub sensitive data before storage
- **Actor Isolation**: User-based memory segregation

### 3. Cognito User Pool (NEW - Following education sample pattern)
**Reference**: `agentcore-for-education/deploy_cognito_user_pool.py`

**Critical Implementation Notes:**
- Create OAuth2 resource server with custom scope: `RestaurantBookingAuth/invoke`
- Configure JWT authorizer with proper discovery URL
- Store client credentials in SSM Parameter Store with encryption
- Create demo users: admin, customer, restaurant_owner
- Implement 15-minute JWT expiry with 7-day refresh tokens
- Enable rate limiting: 100 req/min per user with burst allowance

### 4. AgentCore Gateway (NEW - Following education sample pattern)
**Reference**: `agentcore-for-education/deploy_agentcore_gateway.py`

**Critical Implementation Notes:**
- Create gateway with JWT authorization using Cognito User Pool
- Register 7 MCP tools with exact parameter schemas
- Configure tool definitions matching Lambda function signatures
- Set up proper error handling and timeout configurations (30s max)
- Implement policy gate for tool invocation governance
- Test gateway connectivity before agent runtime deployment

**Tool Registration Schema:**
- fetchRestaurantDetails: city?, cuisine?, priceRange?, minRating?
- fetchRestaurantDetailsById: restaurantId (required)
- searchUserDetails: username?, userMobileNo?
- registerUser: username, mobileNo, userCity, requestId
- tokenAmountCalculation: noOfGuests, mealType?, restaurantTier?
- bookATable: restaurantId, userName, userMobileNo, date, time, type, cityName, noOfGuests, tokenAmount, requestId
- paymentAPI: userId, restaurantId, bookingId?, tokenAmount, paymentMethod?, requestId

### 5. AgentCore Runtime (NEW - Following education sample pattern)
**Reference**: `agentcore-for-education/deploy_agentcore_runtime_with_gw.py`

**Critical Implementation Notes:**
- Create orchestrator agent with proper memory integration
- Configure agent with gateway URL and authentication
- Set up proper IAM roles for agent execution
- Configure CloudWatch logging with correct log group structure
- Enable X-Ray tracing for distributed observability
- Set 8-minute timeout for long-running workflows
- Test agent invocation with sample requests

### 6. Cost-Optimized Model Router (NEW)

**Model Selection Strategy:**
- **Intent Classification**: Nova Micro ($0.00015/1K tokens) - 97% cheaper
- **Restaurant Search**: Nova Lite ($0.0006/1K tokens) - Standard conversations
- **Booking Validation**: Claude Sonnet ($0.003/1K tokens) - High-stakes operations
- **Payment Processing**: Claude Sonnet - Accuracy-critical
- **Complex Reasoning**: Nova Pro - Advanced capabilities

**Implementation Steps:**
1. Create CostOptimizedModelRouter class with model cost matrix
2. Implement task complexity detection
3. Add intelligent prompt routing based on query analysis
4. Enable prompt caching for 90% cost reduction on system prompts
5. Track cost per request with CloudWatch metrics
6. Implement budget controls per user with DynamoDB tracking

### 7. Strands Agents with SOLID Principles (NEW)

**Agent Architecture:**
- **Single Responsibility**: Each agent handles ONE task only
- **Open/Closed**: Base Agent class, extend without modification
- **Liskov Substitution**: Polymorphic LLMProvider (Anthropic, Amazon Nova)
- **Interface Segregation**: Capability-based tool interfaces
- **Dependency Inversion**: Constructor injection of dependencies

**Agent Implementations:**

#### Intent Classifier Agent
- **Model**: Nova Micro (cost-optimized)
- **Temperature**: 0 (deterministic)
- **Responsibility**: Route to appropriate specialist agent
- **Output**: "search" | "booking" | "history" | "payment"

#### Restaurant Finder Agent (Handoff Pattern)
- **Model**: Nova Lite with Claude Haiku fallback
- **Responsibility**: Search and recommend restaurants only
- **Tools**: fetchRestaurantDetails, fetchRestaurantDetailsById
- **Circuit Breaker**: 5 failures → fallback to Nova
- **Caching**: 5-minute result cache for identical queries
- **Handoff**: Transfer context to Booking Agent when booking intent detected

#### Booking Agent (SAGA Pattern)
- **Model**: Claude Sonnet (accuracy-critical)
- **Responsibility**: Booking and payment orchestration
- **SAGA Steps**: User validation → Token calculation → Table booking → Payment
- **Compensation**: Reverse order rollback on failures
- **HITL**: Human approval required for >10 guests
- **Idempotency**: All operations use correlation_id-based request IDs

#### Memory Agent
- **Responsibility**: Conversation persistence and retrieval
- **Storage**: AgentCore Memory with PII scrubbing
- **Retrieval**: Semantic search for "show my Italian bookings"
- **Retention**: 3 days for conversations, permanent for preferences

### 8. LangGraph Workflow Orchestration (NEW)

**State Management:**
- TypedDict schema with correlation_id, user_id, session_id
- Message history with add_messages annotation
- Intent routing with conditional edges
- Error handling with compensation stack tracking
- Memory status and retry count management

**Workflow Nodes:**
- entry_router: Intent classification and routing
- restaurant_finder: Search and recommendation
- booking_agent: Reservation and payment
- memory_agent: Conversation persistence
- error_handler: Graceful failure management

**Conditional Routing:**
- Search intent → Restaurant Finder Agent
- Booking intent → Booking Agent (with context handoff)
- History intent → Memory Agent
- Error conditions → Error Handler with SAGA compensation

### 9. Security & Governance Implementation (NEW)

**Prompt Injection Defense:**
- Input validation with injection pattern detection
- Structured input wrapping: `<user_input>{message}</user_input>`
- System prompt hierarchy enforcement
- Role boundary reinforcement

**Policy-as-Code:**
- Governance policies for each tool with declarative rules
- Max guests: 20, Max token amount: $500
- HITL approval for high-risk operations
- Real-time policy evaluation before tool execution

**PII Protection:**
- Microsoft Presidio integration for detection
- Automatic redaction before memory storage
- Masking in logs and monitoring
- Field-level encryption for sensitive data

### 10. Observability & Monitoring (NEW)

**Comprehensive Tracing:**
- Correlation IDs for end-to-end request tracking
- X-Ray distributed tracing across all components
- Structured logging with agent decision context
- Cost tracking per user, per agent, per request

**Monitoring Dashboard:**
- Request metrics: count, success rate, error rate
- Latency metrics: average, p95, p99
- Cost metrics: per request, total spend, budget alerts
- Agent activity: invocations, tool calls, memory operations
- Error breakdown: by type, frequency, impact

**Alerting Rules:**
- High error rate: >5% triggers alert
- High latency: >5 seconds triggers alert
- High cost: >$1 per request triggers alert
- Budget exceeded: User-level spending limits

## Deployment Strategy

### Phase 1: Infrastructure Foundation (Following Education Sample)
1. **Deploy Lambda Functions** - Copy from backup with idempotency and HITL
2. **Create DynamoDB Tables** - Users, Restaurants, Bookings with GSIs
3. **Deploy AgentCore Memory** - With CloudWatch logging fix and PII scrubbing
4. **Deploy Cognito User Pool** - OAuth2, JWT, demo users, rate limiting
5. **Deploy AgentCore Gateway** - MCP tool registration with policy gates
6. **Deploy AgentCore Runtime** - Memory integration, X-Ray tracing, 8min timeout

### Phase 2: Production Patterns Implementation
1. **Cost-Optimized Model Router** - Nova Micro → Lite → Sonnet routing
2. **Strands Agents with SOLID** - Single responsibility, dependency injection
3. **LangGraph Workflow** - State management, conditional routing, handoff pattern
4. **SAGA Pattern** - Compensation orchestrator with rollback logic
5. **Circuit Breaker** - LLM fallback (Claude → Nova) with 60s timeout
6. **Prompt Versioning** - S3 storage, version pinning, feature flags

### Phase 3: Security & Governance
1. **Prompt Injection Defense** - Input validation, structured wrapping
2. **Policy-as-Code** - Declarative governance rules, HITL workflows
3. **PII Protection** - Presidio integration, automatic redaction
4. **Budget Controls** - Per-user limits, real-time tracking
5. **Audit Logging** - Complete decision trail, compliance ready

### Phase 4: Observability & Optimization
1. **Comprehensive Monitoring** - CloudWatch dashboard, X-Ray tracing
2. **Cost Tracking** - Per-request metrics, budget alerts
3. **Performance Optimization** - Prompt caching, model selection tuning
4. **Load Testing** - 1000 req/min target, chaos engineering
5. **A/B Testing** - Prompt versions, model comparisons

### Phase 5: Production Validation
1. **Unit Tests** - Agent nodes, tool functions, policy enforcement
2. **Integration Tests** - End-to-end workflows, handoff patterns
3. **SAGA Testing** - Compensation scenarios, rollback validation
4. **Circuit Breaker Testing** - LLM fallback scenarios
5. **Security Testing** - Prompt injection, PII protection
6. **Load Testing** - Concurrent users, system limits

## Critical Success Factors

### Memory Implementation
- **CloudWatch Logging**: Explicit IAM permissions for bedrock-agentcore service
- **Service Principal**: Correct trust policy configuration
- **PII Scrubbing**: Automatic redaction before storage
- **Actor Isolation**: User-based memory segregation
- **Retention Policy**: 3 days for conversations, permanent for preferences

### Gateway Implementation
- **JWT Authentication**: Cognito integration with 15-minute expiry
- **Tool Registration**: Exact schema matching Lambda signatures
- **Policy Gates**: Real-time governance rule evaluation
- **Error Handling**: 30s timeout, graceful degradation
- **Idempotency**: Request ID validation and deduplication

### Runtime Implementation
- **Memory Integration**: Proper memory ID and role ARN
- **Gateway Integration**: Authenticated tool invocation
- **Observability**: X-Ray tracing, structured logging
- **Cost Control**: Model routing, budget enforcement
- **Error Recovery**: SAGA compensation, circuit breakers

### Production Readiness
- **Security**: WAF, rate limiting, prompt injection defense
- **Governance**: Policy-as-code, HITL workflows, audit trails
- **Observability**: Correlation IDs, cost tracking, alerting
- **Performance**: Prompt caching, model optimization, load testing
- **Compliance**: PII protection, data retention, audit logging

## File Structure
```
src/
├── agents/                       # Strands Agent implementations
│   ├── intent_classifier.py      # IntentClassifierAgent + node wrapper
│   ├── restaurant_finder.py      # RestaurantFinderAgent + handoff pattern
│   ├── booking_agent.py          # BookingAgent + SAGA pattern
│   └── memory_agent.py           # MemoryAgent + conversation persistence
├── lambda/                       # COPY AS-IS from backup
│   ├── book_a_table.py          # HITL + idempotency + SAGA
│   ├── fetch_restaurant_details.py # Search with filters
│   ├── payment_api.py           # Circuit breaker + compensation
│   └── [all other lambda files]
├── tools/                        # MCP tool wrappers
│   ├── restaurant_tools.py      # fetchRestaurantDetails integration
│   ├── booking_tools.py         # bookATable with policy gates
│   └── user_tools.py            # registerUser with validation
├── workflows/                    # LangGraph orchestration
│   ├── state.py                 # RestaurantBookingState TypedDict
│   └── restaurant_workflow.py   # Handoff pattern + conditional routing
├── utils/                        # Production utilities
│   ├── cost_tracker.py          # Model selection + budget control
│   ├── saga_pattern.py          # Compensation orchestrator
│   ├── circuit_breaker.py       # LLM fallback pattern
│   ├── memory_manager.py        # AgentCore memory + PII scrubbing
│   ├── prompt_loader.py         # S3 versioned prompts
│   ├── policy_engine.py         # Governance rule evaluation
│   └── security.py              # Prompt injection defense
├── config/
│   ├── models.py                # Cost-optimized model matrix
│   └── policies.py              # Governance rule definitions
└── monitoring/
    ├── dashboard.py             # CloudWatch dashboard creation
    └── alerts.py                # Alarm configuration
```

## Dependencies
- strands-agents>=1.0.0 (Agent framework)
- langgraph>=0.2.0 (Workflow orchestration)
- bedrock-agentcore>=1.0.0 (Runtime platform)
- bedrock-agentcore-starter-toolkit>=1.0.0 (Deployment tools)
- boto3>=1.34.0 (AWS SDK)
- aws-xray-sdk>=2.12.0 (Distributed tracing)
- presidio-analyzer>=2.2.0 (PII detection)
- presidio-anonymizer>=2.2.0 (PII redaction)
- pydantic>=2.0.0 (Data validation)
- structlog>=24.0.0 (Structured logging)

## Key Implementation Principles
1. **Copy Lambda Functions As-Is** - Production-tested with idempotency and HITL
2. **Follow Education Sample Patterns** - Proven deployment with CloudWatch fixes
3. **Implement Handoff Pattern** - Restaurant Finder → Booking Agent context transfer
4. **Apply SAGA Pattern** - Compensatable transactions with rollback logic
5. **Cost as First-Class Metric** - Intelligent model routing and budget controls
6. **Security by Design** - Prompt injection defense and PII protection
7. **Comprehensive Observability** - Correlation IDs and distributed tracing
8. **Production Governance** - Policy-as-code and HITL workflows