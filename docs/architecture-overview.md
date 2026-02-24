Architecture Overview
This is a production-grade Restaurant Booking System using a hybrid LangGraph + Strands Agents architecture with AWS Bedrock AgentCore.

Core Design Pattern
Strands Agents (business logic) + LangGraph (orchestration) + MCP Tools (Lambda functions)

User Input → Orchestrator → LangGraph Workflow → Strands Agents → MCP Tools → Response

Copy
Key Components
1. Workflow Orchestration (LangGraph)
RestaurantBookingWorkflow - Main state machine with conditional routing

RestaurantBookingState - TypedDict schema for state management

Routes: entry_router → restaurant_finder → booking_agent → error_handler

Integrates AgentCore Memory for conversation persistence

2. Specialized Agents (Strands)
Each agent follows Single Responsibility Principle:

IntentClassifierAgent - Routes queries (uses Nova Micro for 97% cost savings)

RestaurantFinderAgent - Searches restaurants, implements handoff pattern

BookingAgent - Executes bookings with SAGA pattern for transaction safety

GreetingAgent - Personalized greetings

3. Core Infrastructure
Base Agent - Abstract class with LLM invocation, input validation, cost tracking

LLM Providers - Polymorphic providers (Nova, Claude) with Circuit Breaker fallback

CostOptimizedModelRouter - Task-based model selection (Micro → Lite → Sonnet)

PromptManager - Versioned prompts from S3

4. MCP Tools (Lambda Functions)
fetchRestaurantDetails - Search restaurants

bookATable - Create reservation

registerUser - User registration

paymentAPI - Process payments

getCurrentDateTime - Date/time for bookings

All tools support idempotency via requestId

Key Patterns Implemented
SAGA Pattern (Booking Agent)
User Validation → Registration → Token Calc → Table Booking → Payment
                    ↓ (on failure)
              Compensation Stack (rollback in reverse)

Copy
Circuit Breaker
Primary LLM (Claude) fails → Fallback to Secondary (Nova)

Copy
Handoff Pattern
RestaurantFinder detects booking intent → Hands off to BookingAgent with context

Copy
Memory Integration
Stores conversation history in AgentCore Memory

Retrieves partial booking params across turns

Prevents duplicate bookings via booking_completed flag

Cost Optimization
Task-based model selection:

Intent classification: Nova Micro ($0.000035/1K tokens)

Restaurant search: Nova Lite ($0.00006/1K tokens)

Booking validation: Claude Sonnet ($0.003/1K tokens)

Security Features
Prompt injection validation with regex patterns

Input wrapping with <user_input> tags

Guardrails (optional, disabled for booking agent to allow phone numbers)

Idempotency on all tool calls

Observability
Correlation IDs for request tracing

X-Ray tracing support

Cost tracking per operation

Compensation logs for SAGA rollbacks

The codebase follows SOLID principles, uses dependency injection, and maintains clear separation between orchestration (LangGraph) and business logic (Strands Agents).