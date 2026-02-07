# Restaurant Booking System - Detailed Task Execution List

## Task Execution Order

### Phase 1: Infrastructure Foundation (Days 1-3)

#### Task 1.1: Copy Lambda Functions from Backup
**Duration**: 2 hours
**Dependencies**: None
**Steps**:
1. Copy entire `/Users/USER/Work/AI/AgentCore/ResturantBookingSystem_backup/src/lambda/` directory
2. Verify all 10 files are present:
   - `book_a_table.py`, `book_restaurant.py`, `fetch_restaurant_details.py`
   - `fetch_restaurant_details_by_id.py`, `register_user.py`, `search_user_details.py`
   - `payment_api.py`, `token_amount_calculation.py`, `utils.py`, `circuit_breaker.py`
3. Review `requirements.txt` for dependencies
4. Test syntax validation: `python -m py_compile *.py`

#### Task 1.2: Copy SAM Template from Backup and Create DynamoDB Tables
**Duration**: 3 hours
**Dependencies**: Task 1.1
**Steps**:
1. Copy `template.yaml` from backup: `/Users/USER/Work/AI/AgentCore/ResturantBookingSystem_backup/template.yaml`
2. Update SAM template to align with existing DynamoDB tables:
   - `Restaurants` table with GSIs: `CityIndex` (city+rating), `CuisineIndex` (cuisine+rating)
   - `Users` table with GSIs: `MobileIndex` (mobileNo), `UsernameIndex` (username)
   - `Bookings` table with GSIs: `UserBookingsIndex` (userId+createdAt), `RestaurantBookingsIndex` (restaurantId+bookingDate), `DateIndex` (bookingDate+bookingTime)
   - `Payments` table with GSIs: `BookingPaymentIndex` (bookingId), `UserPaymentIndex` (userId+paymentDate)
   - `IdempotencyCache` table for request deduplication (may need creation)
   - `UserBudgets` table for cost control (may need creation)
3. Update Lambda function configurations:
   - Change runtime from python3.9 to python3.11
   - Add ARM64 architecture for cost optimization
   - Update environment variables for all tables
4. Create `samconfig.toml` for deployment configuration
5. Validate SAM template: `sam validate`
6. Test local build: `sam build`

#### Task 1.3: Deploy Infrastructure with SAM ✅ COMPLETED
**Duration**: 2 hours
**Dependencies**: Task 1.2
**Steps**:
1. ✅ Deploy SAM stack: `sam deploy --guided`
2. ✅ Verify DynamoDB tables creation with correct GSIs
3. ✅ Verify Lambda functions deployment with proper IAM roles
   - All 8 Lambda functions deployed with python3.11 runtime and ARM64 architecture
   - Proper IAM roles with DynamoDB permissions for all tables
   - Environment variables correctly configured
   - Test execution successful (fetchRestaurantDetails-dev returned Italian Bistro data)
4. Test each Lambda function individually using SAM local
5. Insert test restaurant data using `add_test_restaurant.py`
6. Record Lambda ARNs from CloudFormation outputs
7. Validate all environment variables are set correctly

#### Task 1.4: Deploy AgentCore Memory
**Duration**: 2 hours
**Dependencies**: None
**Reference**: `agentcore-for-education/deploy_agentcore_memory.py`
**Steps**:
1. Create IAM role with CloudWatch permissions:
   - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
2. Set trust policy for `bedrock-agentcore.amazonaws.com`
3. Deploy memory with 3-day retention policy
4. Configure PII scrubbing settings
5. Test memory creation with validation script
6. Record Memory ID and Role ARN

#### Task 1.5: Deploy Cognito User Pool
**Duration**: 2 hours
**Dependencies**: None
**Reference**: `agentcore-for-education/deploy_cognito_user_pool.py`
**Steps**:
1. Create Cognito User Pool with OAuth2 configuration
2. Create resource server with scope: `RestaurantBookingAuth/invoke`
3. Configure JWT authorizer with discovery URL
4. Create demo users: admin, customer, restaurant_owner
5. Store client credentials in SSM Parameter Store
6. Test authentication flow
7. Record User Pool ID and Client ID

### Phase 2: AgentCore Platform Setup (Days 4-5)

#### Task 2.1: Deploy AgentCore Gateway
**Duration**: 4 hours
**Dependencies**: Task 1.3, Task 1.5
**Reference**: `agentcore-for-education/deploy_agentcore_gateway.py`
**Steps**:
1. Create gateway with JWT authorization from Cognito
2. Register 7 MCP tools with exact schemas using Lambda ARNs from SAM outputs:
   - `fetchRestaurantDetails`: city?, cuisine?, priceRange?, minRating?
   - `fetchRestaurantDetailsById`: restaurantId (required)
   - `searchUserDetails`: username?, userMobileNo?
   - `registerUser`: username, mobileNo, userCity, requestId
   - `tokenAmountCalculation`: noOfGuests, mealType?, restaurantTier?
   - `bookATable`: restaurantId, userName, userMobileNo, date, time, type, cityName, noOfGuests, tokenAmount, requestId
   - `paymentAPI`: userId, restaurantId, bookingId?, tokenAmount, paymentMethod?, requestId
3. Configure 30s timeout for all tools
4. Test gateway connectivity with sample requests
5. Record Gateway ID and URL

#### Task 2.2: Deploy AgentCore Runtime
**Duration**: 3 hours
**Dependencies**: Task 1.4, Task 2.1
**Reference**: `agentcore-for-education/deploy_agentcore_runtime_with_gw.py`
**Steps**:
1. Create orchestrator agent configuration
2. Integrate with Memory ID and Gateway URL
3. Set up IAM roles for agent execution
4. Configure CloudWatch logging with proper log groups
5. Enable X-Ray tracing
6. Set 8-minute timeout for workflows
7. Test agent invocation with sample request
8. Record Agent Runtime ARN

### Phase 3: Cost Optimization & Model Router (Day 6)

#### Task 3.1: Implement Cost-Optimized Model Router
**Duration**: 4 hours
**Dependencies**: None
**Steps**:
1. Create `src/utils/cost_tracker.py`:
   - Model cost matrix (Nova Micro: $0.00015, Nova Lite: $0.0006, Claude Sonnet: $0.003)
   - Task complexity detection logic
   - Model selection based on task type
2. Implement intelligent routing:
   - Intent classification → Nova Micro
   - Restaurant search → Nova Lite
   - Booking validation → Claude Sonnet
   - Payment processing → Claude Sonnet
3. Add cost estimation and tracking functions
4. Create CloudWatch metrics for cost monitoring
5. Test model selection logic

#### Task 3.2: Budget Controls Already in SAM Template
**Duration**: 1 hour
**Dependencies**: Task 3.1
**Steps**:
1. Verify `UserBudgets` table is already included in SAM template
2. Implement budget checking logic in `cost_tracker.py`
3. Add per-user spending limits ($10 default)
4. Create budget exceeded error handling
5. Test budget enforcement

### Phase 4: Strands Agents Implementation (Days 7-9)

#### Task 4.1: Create Base Agent Architecture
**Duration**: 3 hours
**Dependencies**: Task 3.1
**Steps**:
1. Create `src/utils/llm_providers.py`:
   - Abstract `LLMProvider` base class
   - `AnthropicProvider` implementation
   - `AmazonNovaProvider` implementation
2. Implement dependency injection pattern
3. Create base `Agent` class following SOLID principles
4. Test provider switching and polymorphism

#### Task 4.2: Implement Intent Classifier Agent
**Duration**: 2 hours
**Dependencies**: Task 4.1
**Steps**:
1. Create `src/agents/intent_classifier.py`:
   - `IntentClassifierAgent` class using Nova Micro
   - Temperature=0 for deterministic output
   - Intent detection: "search" | "booking" | "history" | "payment"
2. Create LangGraph node wrapper function
3. Test intent classification accuracy
4. Validate cost optimization (97% cheaper than Claude)

#### Task 4.3: Implement Restaurant Finder Agent
**Duration**: 4 hours
**Dependencies**: Task 4.2, Task 2.1
**Steps**:
1. Create `src/agents/restaurant_finder.py`:
   - `RestaurantFinderAgent` class using Nova Lite
   - Circuit breaker for Claude Haiku fallback
   - Tool integration: `fetchRestaurantDetails`, `fetchRestaurantDetailsById`
2. Implement 5-minute result caching
3. Add handoff detection for booking intent
4. Create LangGraph node wrapper
5. Test search functionality and fallback mechanism

#### Task 4.4: Implement Booking Agent with SAGA Pattern
**Duration**: 6 hours
**Dependencies**: Task 4.3
**Steps**:
1. Create `src/utils/saga_pattern.py`:
   - `SagaOrchestrator` class
   - Compensation stack management
   - Rollback logic in reverse order
2. Create `src/agents/booking_agent.py`:
   - `BookingAgent` class using Claude Sonnet
   - SAGA steps: User validation → Token calc → Booking → Payment
   - HITL workflow for >10 guests
   - Idempotency with correlation_id-based request IDs
3. Implement compensation handlers
4. Test SAGA rollback scenarios
5. Validate HITL approval workflow

#### Task 4.5: Implement Memory Agent
**Duration**: 2 hours
**Dependencies**: Task 1.4
**Steps**:
1. Create `src/utils/memory_manager.py`:
   - AgentCore Memory integration
   - PII scrubbing before storage
   - Actor-based isolation
2. Create `src/agents/memory_agent.py`:
   - Conversation persistence
   - Semantic search for history queries
   - 3-day retention for conversations
3. Test memory operations and PII protection

### Phase 5: LangGraph Workflow Orchestration (Day 10)

#### Task 5.1: Create State Management
**Duration**: 2 hours
**Dependencies**: Task 4.5
**Steps**:
1. Create `src/workflows/state.py`:
   - `RestaurantBookingState` TypedDict
   - Message history with `add_messages` annotation
   - Correlation ID, user ID, session ID tracking
   - Error handling and retry count fields
2. Test state schema validation

#### Task 5.2: Implement LangGraph Workflow
**Duration**: 4 hours
**Dependencies**: Task 5.1
**Steps**:
1. Create `src/workflows/restaurant_workflow.py`:
   - StateGraph with conditional routing
   - Entry router for intent classification
   - Handoff pattern: Restaurant Finder → Booking Agent
   - Error handler with SAGA compensation
2. Configure conditional edges based on intent
3. Test end-to-end workflow execution
4. Validate context transfer between agents

### Phase 6: Security & Governance (Days 11-12)

#### Task 6.1: Implement Prompt Injection Defense
**Duration**: 3 hours
**Dependencies**: None
**Steps**:
1. Create `src/utils/security.py`:
   - Input validation with injection pattern detection
   - Structured input wrapping: `<user_input>{message}</user_input>`
   - System prompt hierarchy enforcement
2. Test against common injection attacks
3. Validate role boundary enforcement

#### Task 6.2: Implement Policy-as-Code
**Duration**: 4 hours
**Dependencies**: Task 6.1
**Steps**:
1. Create `src/utils/policy_engine.py`:
   - Declarative governance rules
   - Max guests: 20, Max token amount: $500
   - HITL approval triggers
   - Real-time policy evaluation
2. Create `src/config/policies.py` with rule definitions
3. Test policy enforcement for all tools
4. Validate HITL workflow integration

#### Task 6.3: Implement PII Protection
**Duration**: 3 hours
**Dependencies**: Task 6.2
**Steps**:
1. Install Microsoft Presidio dependencies
2. Enhance `memory_manager.py` with PII detection
3. Add automatic redaction before storage
4. Implement masking in logs and monitoring
5. Test PII protection across all data flows

### Phase 7: Observability & Monitoring (Day 13)

#### Task 7.1: Implement Comprehensive Tracing
**Duration**: 4 hours
**Dependencies**: Task 5.2
**Steps**:
1. Add correlation ID generation and propagation
2. Implement X-Ray tracing across all components
3. Create structured logging with agent decision context
4. Add cost tracking per user/agent/request
5. Test distributed tracing end-to-end

#### Task 7.2: Create Monitoring Dashboard
**Duration**: 3 hours
**Dependencies**: Task 7.1
**Steps**:
1. Create `src/monitoring/dashboard.py`:
   - CloudWatch dashboard configuration
   - Request metrics: count, success rate, error rate
   - Latency metrics: average, p95, p99
   - Cost metrics: per request, total spend
   - Agent activity and tool invocations
2. Deploy dashboard to CloudWatch
3. Test metric collection and visualization

#### Task 7.3: Configure Alerting
**Duration**: 2 hours
**Dependencies**: Task 7.2
**Steps**:
1. Create `src/monitoring/alerts.py`:
   - High error rate: >5% triggers alert
   - High latency: >5 seconds triggers alert
   - High cost: >$1 per request triggers alert
   - Budget exceeded alerts
2. Configure SNS topics for notifications
3. Test alert triggering and notifications

### Phase 8: Integration & Testing (Days 14-15)

#### Task 8.1: Unit Testing
**Duration**: 6 hours
**Dependencies**: All previous tasks
**Steps**:
1. Create unit tests for each agent node
2. Test tool functions with mocked dependencies
3. Test policy enforcement scenarios
4. Test SAGA compensation logic
5. Test circuit breaker fallback
6. Achieve >80% code coverage

#### Task 8.2: Integration Testing
**Duration**: 4 hours
**Dependencies**: Task 8.1
**Steps**:
1. Test end-to-end workflow scenarios
2. Test handoff pattern between agents
3. Test memory persistence across sessions
4. Test concurrent user scenarios
5. Validate cost tracking accuracy

#### Task 8.3: Load Testing
**Duration**: 4 hours
**Dependencies**: Task 8.2
**Steps**:
1. Create Locust load testing scripts
2. Test system with 100 concurrent users
3. Validate 1000 req/min target performance
4. Test system behavior under load
5. Identify and fix performance bottlenecks

### Phase 9: Production Deployment (Day 16)

#### Task 9.1: Production Configuration
**Duration**: 2 hours
**Dependencies**: Task 8.3
**Steps**:
1. Create production environment variables
2. Configure production IAM roles and policies
3. Set up production DynamoDB tables
4. Configure production Cognito settings
5. Update all ARNs and endpoints for production

#### Task 9.2: Final Deployment
**Duration**: 3 hours
**Dependencies**: Task 9.1
**Steps**:
1. Deploy all components to production environment
2. Run smoke tests on production system
3. Validate all integrations working correctly
4. Test with real user scenarios
5. Monitor system health and performance

#### Task 9.3: Documentation & Handover
**Duration**: 3 hours
**Dependencies**: Task 9.2
**Steps**:
1. Create operational runbooks
2. Document troubleshooting procedures
3. Create user guides and API documentation
4. Set up monitoring and alerting procedures
5. Conduct knowledge transfer session

## SAM Template (Copy from Backup)

**Source**: `/Users/USER/Work/AI/AgentCore/ResturantBookingSystem_backup/template.yaml`

**Enhanced SAM Template with DynamoDB Tables:**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Restaurant Booking System with DynamoDB Tables and Lambda Functions

Globals:
  Function:
    Timeout: 30
    Runtime: python3.11
    Architectures:
      - arm64
    Environment:
      Variables:
        RESTAURANTS_TABLE: !Ref RestaurantsTable
        USERS_TABLE: !Ref UsersTable
        BOOKINGS_TABLE: !Ref BookingsTable
        PAYMENTS_TABLE: !Ref PaymentsTable
        IDEMPOTENCY_TABLE: !Ref IdempotencyTable
        USER_BUDGETS_TABLE: !Ref UserBudgetsTable

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]

Resources:
  # DynamoDB Tables
  RestaurantsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "Restaurants-${Environment}"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: restaurantId
          AttributeType: S
        - AttributeName: city
          AttributeType: S
        - AttributeName: cuisine
          AttributeType: S
      KeySchema:
        - AttributeName: restaurantId
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: CityIndex
          KeySchema:
            - AttributeName: city
              KeyType: HASH
          Projection:
            ProjectionType: ALL
        - IndexName: CuisineIndex
          KeySchema:
            - AttributeName: cuisine
              KeyType: HASH
          Projection:
            ProjectionType: ALL

  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "Users-${Environment}"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: userId
          AttributeType: S
        - AttributeName: mobileNo
          AttributeType: S
        - AttributeName: username
          AttributeType: S
      KeySchema:
        - AttributeName: userId
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: MobileIndex
          KeySchema:
            - AttributeName: mobileNo
              KeyType: HASH
          Projection:
            ProjectionType: ALL
        - IndexName: UsernameIndex
          KeySchema:
            - AttributeName: username
              KeyType: HASH
          Projection:
            ProjectionType: ALL

  BookingsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "Bookings-${Environment}"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: bookingId
          AttributeType: S
        - AttributeName: userId
          AttributeType: S
        - AttributeName: restaurantId
          AttributeType: S
      KeySchema:
        - AttributeName: bookingId
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: UserIndex
          KeySchema:
            - AttributeName: userId
              KeyType: HASH
          Projection:
            ProjectionType: ALL
        - IndexName: RestaurantIndex
          KeySchema:
            - AttributeName: restaurantId
              KeyType: HASH
          Projection:
            ProjectionType: ALL

  PaymentsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "Payments-${Environment}"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: paymentId
          AttributeType: S
      KeySchema:
        - AttributeName: paymentId
          KeyType: HASH

  IdempotencyTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "IdempotencyCache-${Environment}"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: requestId
          AttributeType: S
      KeySchema:
        - AttributeName: requestId
          KeyType: HASH
      TimeToLiveSpecification:
        AttributeName: ttl
        Enabled: true

  UserBudgetsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "UserBudgets-${Environment}"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: userId
          AttributeType: S
      KeySchema:
        - AttributeName: userId
          KeyType: HASH

  # Lambda Functions (from backup template)
  FetchRestaurantDetailsFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "fetchRestaurantDetails-${Environment}"
      CodeUri: src/lambda/
      Handler: fetch_restaurant_details.lambda_handler
      Timeout: 5
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref RestaurantsTable

  FetchRestaurantDetailsByIdFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "fetchRestaurantDetailsById-${Environment}"
      CodeUri: src/lambda/
      Handler: fetch_restaurant_details_by_id.lambda_handler
      Timeout: 3
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref RestaurantsTable

  BookATableFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "bookATable-${Environment}"
      CodeUri: src/lambda/
      Handler: book_a_table.lambda_handler
      Timeout: 10
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref BookingsTable
        - DynamoDBReadPolicy:
            TableName: !Ref RestaurantsTable
        - DynamoDBCrudPolicy:
            TableName: !Ref IdempotencyTable

  SearchUserDetailsFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "searchUserDetails-${Environment}"
      CodeUri: src/lambda/
      Handler: search_user_details.lambda_handler
      Timeout: 3
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref UsersTable

  RegisterUserFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "registerUser-${Environment}"
      CodeUri: src/lambda/
      Handler: register_user.lambda_handler
      Timeout: 5
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable
        - DynamoDBCrudPolicy:
            TableName: !Ref IdempotencyTable

  TokenAmountCalculationFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "tokenAmountCalculation-${Environment}"
      CodeUri: src/lambda/
      Handler: token_amount_calculation.lambda_handler
      Timeout: 2

  PaymentAPIFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "paymentAPI-${Environment}"
      CodeUri: src/lambda/
      Handler: payment_api.lambda_handler
      Timeout: 15
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref PaymentsTable
        - DynamoDBCrudPolicy:
            TableName: !Ref IdempotencyTable

Outputs:
  # DynamoDB Table Names
  RestaurantsTableName:
    Description: "Restaurants DynamoDB Table Name"
    Value: !Ref RestaurantsTable
    Export:
      Name: !Sub "${AWS::StackName}-RestaurantsTable"

  UsersTableName:
    Description: "Users DynamoDB Table Name"
    Value: !Ref UsersTable
    Export:
      Name: !Sub "${AWS::StackName}-UsersTable"

  BookingsTableName:
    Description: "Bookings DynamoDB Table Name"
    Value: !Ref BookingsTable
    Export:
      Name: !Sub "${AWS::StackName}-BookingsTable"

  # Lambda Function ARNs (for AgentCore Gateway registration)
  FetchRestaurantDetailsFunctionArn:
    Description: "Fetch Restaurant Details Lambda Function ARN"
    Value: !GetAtt FetchRestaurantDetailsFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-FetchRestaurantDetailsFunction"

  FetchRestaurantDetailsByIdFunctionArn:
    Description: "Fetch Restaurant Details By ID Lambda Function ARN"
    Value: !GetAtt FetchRestaurantDetailsByIdFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-FetchRestaurantDetailsByIdFunction"

  BookATableFunctionArn:
    Description: "Book A Table Lambda Function ARN"
    Value: !GetAtt BookATableFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-BookATableFunction"

  SearchUserDetailsFunctionArn:
    Description: "Search User Details Lambda Function ARN"
    Value: !GetAtt SearchUserDetailsFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-SearchUserDetailsFunction"

  RegisterUserFunctionArn:
    Description: "Register User Lambda Function ARN"
    Value: !GetAtt RegisterUserFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-RegisterUserFunction"

  TokenAmountCalculationFunctionArn:
    Description: "Token Amount Calculation Lambda Function ARN"
    Value: !GetAtt TokenAmountCalculationFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-TokenAmountCalculationFunction"

  PaymentAPIFunctionArn:
    Description: "Payment API Lambda Function ARN"
    Value: !GetAtt PaymentAPIFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-PaymentAPIFunction"
```

**SAM Deployment Commands:**
```bash
# Build and deploy
sam build
sam deploy --guided

# Local testing
sam local start-api
sam local invoke FetchRestaurantDetailsFunction --event events/test-event.json

# Cleanup
sam delete
```

```
Phase 1: Infrastructure Foundation
├── Task 1.1: Copy Lambda Functions (2h)
├── Task 1.2: Create DynamoDB Tables (1h) → depends on 1.1
├── Task 1.3: Deploy Lambda Functions (3h) → depends on 1.2
├── Task 1.4: Deploy AgentCore Memory (2h)
└── Task 1.5: Deploy Cognito User Pool (2h)

Phase 2: AgentCore Platform Setup
├── Task 2.1: Deploy AgentCore Gateway (4h) → depends on 1.3, 1.5
└── Task 2.2: Deploy AgentCore Runtime (3h) → depends on 1.4, 2.1

Phase 3: Cost Optimization
├── Task 3.1: Implement Model Router (4h)
└── Task 3.2: Implement Budget Controls (2h) → depends on 3.1

Phase 4: Strands Agents
├── Task 4.1: Base Agent Architecture (3h) → depends on 3.1
├── Task 4.2: Intent Classifier Agent (2h) → depends on 4.1
├── Task 4.3: Restaurant Finder Agent (4h) → depends on 4.2, 2.1
├── Task 4.4: Booking Agent with SAGA (6h) → depends on 4.3
└── Task 4.5: Memory Agent (2h) → depends on 1.4

Phase 5: LangGraph Workflow
├── Task 5.1: State Management (2h) → depends on 4.5
└── Task 5.2: LangGraph Workflow (4h) → depends on 5.1

Phase 6: Security & Governance
├── Task 6.1: Prompt Injection Defense (3h)
├── Task 6.2: Policy-as-Code (4h) → depends on 6.1
└── Task 6.3: PII Protection (3h) → depends on 6.2

Phase 7: Observability
├── Task 7.1: Comprehensive Tracing (4h) → depends on 5.2
├── Task 7.2: Monitoring Dashboard (3h) → depends on 7.1
└── Task 7.3: Configure Alerting (2h) → depends on 7.2

Phase 8: Testing
├── Task 8.1: Unit Testing (6h) → depends on all previous
├── Task 8.2: Integration Testing (4h) → depends on 8.1
└── Task 8.3: Load Testing (4h) → depends on 8.2

Phase 9: Production Deployment
├── Task 9.1: Production Configuration (2h) → depends on 8.3
├── Task 9.2: Final Deployment (3h) → depends on 9.1
└── Task 9.3: Documentation & Handover (3h) → depends on 9.2
```

## Total Estimated Duration: 16 days (128 hours)

## Critical Path Tasks:
1. Task 1.1 → 1.2 → 1.3 → 2.1 → 2.2 (Infrastructure setup)
2. Task 3.1 → 4.1 → 4.2 → 4.3 → 4.4 (Agent development)
3. Task 5.1 → 5.2 (Workflow orchestration)
4. Task 8.1 → 8.2 → 8.3 → 9.1 → 9.2 (Testing and deployment)

## Risk Mitigation:
- **CloudWatch Logging Issues**: Follow education sample exactly for memory deployment
- **Gateway Registration**: Test each tool individually before runtime deployment
- **SAGA Compensation**: Implement comprehensive rollback testing
- **Cost Overruns**: Implement budget controls early in development
- **Performance Issues**: Conduct load testing before production deployment