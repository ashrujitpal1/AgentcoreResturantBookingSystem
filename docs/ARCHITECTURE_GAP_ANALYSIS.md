# Architecture Gap Analysis
## Comparing Codebase vs Architecture Diagram

**Analysis Date:** 2024
**Diagram:** `architecture-diagram.eraser`
**Codebase:** `AgentcoreResturantBookingSystem/`

---

## ✅ IMPLEMENTED COMPONENTS

### 1. Core Agents (Strands)
- ✅ **IntentClassifierAgent** - `src/agents/intent_classifier.py`
- ✅ **RestaurantFinderAgent** - `src/agents/restaurant_finder.py`
- ✅ **BookingAgent** - `src/agents/booking_agent.py`
- ✅ **GreetingAgent** - `src/agents/greeting_agent.py`

### 2. LangGraph Workflow
- ✅ **RestaurantBookingState** - `src/workflows/state.py`
- ✅ **RestaurantBookingWorkflow** - `src/workflows/restaurant_workflow.py`
- ✅ **Conditional Routing** - Entry router, search/booking flows
- ✅ **Node Wrappers** - `_entry_router_node`, `_restaurant_finder_node`, `_booking_agent_node`

### 3. Cost-Optimized LLM Selection
- ✅ **CostOptimizedModelRouter** - `src/core/model_router.py`
- ✅ **Nova Micro** - Intent classification
- ✅ **Nova Lite** - Restaurant search
- ✅ **Nova Pro** - Booking validation
- ✅ **Circuit Breaker** - `src/core/llm_provider.py` + `src/lambda/circuit_breaker.py`

### 4. MCP Tools
- ✅ **fetchRestaurantDetails** - `src/lambda/fetch_restaurant_details.py`
- ✅ **searchUserDetails** - `src/lambda/search_user_details.py`
- ✅ **registerUser** - `src/lambda/register_user.py`
- ✅ **bookATable** - `src/lambda/book_a_table.py`
- ✅ **paymentAPI** - `src/lambda/payment_api.py`
- ✅ **getCurrentDateTime** - `src/lambda/get_current_datetime.py`

### 5. SAGA Pattern
- ✅ **Compensation Stack** - `BookingAgent._execute_saga()`
- ✅ **Rollback Logic** - `BookingAgent._compensate()`
- ✅ **Transaction Safety** - Step-by-step with compensation

### 6. Security
- ✅ **Input Validator** - `src/security/governance.py` (PromptInjectionDefense)
- ✅ **Guardrails** - Bedrock Guardrails integration
- ✅ **PII Scrubbing** - `PIIScrubber` class
- ✅ **Policy Gate** - `PolicyGate` for governance

### 7. AgentCore Memory
- ✅ **Conversation History** - `_retrieve_memory()` in workflow
- ✅ **Booking State** - Partial params persistence
- ✅ **Memory Integration** - `_store_memory()` after each turn

### 8. Observability
- ✅ **X-Ray Tracing** - `src/observability/tracing.py`
- ✅ **CloudWatch Logs** - Lambda logging
- ✅ **Cost Tracker** - Token usage tracking in agents

### 9. Frontend
- ✅ **Streamlit Frontend** - `frontend-agentcore/app.py`
- ✅ **Cognito Integration** - User authentication

### 10. Prompt Management
- ✅ **S3 Prompts** - `prompts/` directory with versioning
- ✅ **PromptManager** - `src/core/prompt_manager.py`
- ✅ **Version Pinning** - v1.0.0 for all agents

---

## ❌ MISSING COMPONENTS (Critical Gaps)

### 1. **AgentCore Gateway - Partial Implementation** ⚠️ MEDIUM PRIORITY
**Diagram Shows:**
- Orchestrator Lambda → AgentCore Gateway
- AgentCore Gateway → MCP Tool Functions
- Gateway with Cognito JWT Authorization

**Current State:**
- ✅ Gateway deployment script exists (`deploy_agentcore_gateway.py`)
- ✅ Gateway configured with Cognito JWT auth
- ✅ All 8 MCP tools registered (fetch, search, register, book, payment, datetime)
- ⚠️ **BUT: Tools invoked directly via Lambda, NOT through Gateway**
- ❌ `MCPToolClient` in `src/tools/mcp_client.py` calls Lambda directly
- ❌ No Gateway URL usage in agents
- ❌ No JWT token passing to Gateway

**Impact:**
- Gateway exists but is bypassed
- Missing centralized auth/rate limiting
- No unified observability through Gateway
- Agents don't benefit from Gateway features

**Required Fix:**
```python
# src/tools/mcp_client.py - CURRENT (Wrong)
class MCPToolClient:
    def invoke_lambda(self, function_name: str, payload: Dict):
        return self.lambda_client.invoke(FunctionName=function_name, ...)

# SHOULD BE (Correct)
class MCPToolClient:
    def __init__(self):
        self.gateway_url = os.getenv('GATEWAY_URL')
        self.jwt_token = self._get_cognito_token()
    
    def invoke_tool(self, tool_name: str, payload: Dict):
        response = requests.post(
            f"{self.gateway_url}/tools/{tool_name}",
            json=payload,
            headers={"Authorization": f"Bearer {self.jwt_token}"}
        )
        return response.json()
```

---

### 2. **Cognito User Tier - Partial Implementation** ⚠️ MEDIUM PRIORITY
**Diagram Shows:**
- Cognito User Pool → User Tier
- User Group Validator
- Tier-based access control

**Current State:**
- ✅ Cognito User Pool created
- ✅ Custom attribute `custom:tier` added (manual step required)
- ✅ Test users with tiers: `normal_user`, `gold_user`
- ✅ JWT tokens include tier claim
- ❌ **No tier validation in application code**
- ❌ No `UserTierValidator` class
- ❌ No tier-based feature gating
- ❌ Frontend doesn't extract/use tier from JWT

**Impact:**
- Tier attribute exists but unused
- All users have same access regardless of tier
- No monetization strategy
- Weather API tier logic not enforced

**Required Implementation:**
```python
# src/security/user_tier.py (NEW FILE)
class UserTierValidator:
    TIER_PERMISSIONS = {
        "normal": {
            "max_bookings_per_month": 3,
            "weather_access": True,
            "forecast_access": False
        },
        "gold": {
            "max_bookings_per_month": 20,
            "weather_access": True,
            "forecast_access": True
        },
        "premium": {
            "max_bookings_per_month": -1,  # Unlimited
            "weather_access": True,
            "forecast_access": True,
            "priority_support": True
        }
    }
    
    def validate_feature_access(self, user_tier: str, feature: str) -> bool:
        permissions = self.TIER_PERMISSIONS.get(user_tier, self.TIER_PERMISSIONS["normal"])
        return permissions.get(feature, False)
    
    def check_booking_limit(self, user_id: str, user_tier: str) -> Tuple[bool, str]:
        # Query DynamoDB for user's booking count this month
        # Compare against tier limit
        pass

# src/workflows/restaurant_workflow.py - ADD
from src.security.user_tier import UserTierValidator

class RestaurantBookingWorkflow:
    def __init__(self, mcp_tools):
        self.tier_validator = UserTierValidator()
    
    def _booking_agent_node(self, state):
        # Extract tier from JWT (passed in context)
        user_tier = state.get('context', {}).get('user_tier', 'normal')
        
        # Validate booking limit
        can_book, reason = self.tier_validator.check_booking_limit(
            state['user_id'], user_tier
        )
        if not can_book:
            return {"error": reason, "final_response": reason}
        
        # Continue with booking...
```

**Frontend Integration Needed:**
```python
# frontend-agentcore/app.py - ADD JWT extraction
import jwt
import requests

def get_cognito_token(username: str, password: str):
    # Authenticate with Cognito
    response = requests.post(
        f"https://cognito-idp.{region}.amazonaws.com/",
        json={
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": os.getenv('CLIENT_ID'),
            "AuthParameters": {"USERNAME": username, "PASSWORD": password}
        }
    )
    return response.json()['AuthenticationResult']['IdToken']

def extract_user_tier(token: str) -> str:
    decoded = jwt.decode(token, options={"verify_signature": False})
    return decoded.get('custom:tier', 'normal')

# In Streamlit app
if 'jwt_token' not in st.session_state:
    # Show login form
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        token = get_cognito_token(username, password)
        st.session_state.jwt_token = token
        st.session_state.user_tier = extract_user_tier(token)
```

---

### 3. **WeatherAgent** ⚠️ HIGH PRIORITY
**Diagram Shows:**
- WeatherAgent [icon: cloud, color: cyan]
- Weather Analysis → Bad Weather Detection → Forecast Range Calculator
- weatherAPI and forecastAPI MCP tools

**Current State:**
- ❌ No `WeatherAgent` class in `src/agents/`
- ❌ No weather analysis logic
- ❌ No bad weather detection
- ❌ No forecast range calculator
- ✅ Mock weather service exists (`mock-weather-service/`)
- ❌ Not integrated into LangGraph workflow

**Impact:**
- Missing key differentiator feature
- No weather-based recommendations
- Incomplete user experience

**Required Implementation:**
```python
# src/agents/weather_agent.py
class WeatherAgent(Agent):
    def __init__(self, mcp_tools):
        # Use Nova Lite for weather analysis
        primary, fallback, breaker, config = CostOptimizedModelRouter.get_providers_for_task("restaurant_search")
        super().__init__(name="weather_agent", ...)
        self.mcp_tools = mcp_tools
    
    def process(self, city: str, date: str, correlation_id: str):
        # 1. Call weatherAPI tool
        # 2. Analyze weather conditions
        # 3. Detect bad weather (rain, snow, extreme temps)
        # 4. Calculate forecast range if needed
        # 5. Return weather insights
```

**Workflow Integration Needed:**
```python
# In restaurant_workflow.py
workflow.add_node("weather_agent", self._weather_agent_node)
workflow.add_edge("restaurant_finder", "weather_agent")
workflow.add_edge("weather_agent", "booking_agent")
```

---

### 2. **Weather MCP Tools** ⚠️ HIGH PRIORITY
**Diagram Shows:**
- weatherAPI [icon: server]
- forecastAPI [icon: server]

**Current State:**
- ❌ No `src/lambda/weather_api.py`
- ❌ No `src/lambda/forecast_api.py`
- ✅ Mock service exists but not deployed as Lambda

**Required Implementation:**
```python
# src/lambda/weather_api.py
def lambda_handler(event, context):
    city = event['city']
    date = event['date']
    # Call mock weather service or real API
    # Return current weather conditions
    
# src/lambda/forecast_api.py
def lambda_handler(event, context):
    city = event['city']
    start_date = event['startDate']
    end_date = event['endDate']
    # Return 7-day forecast
```

---

### 3. **Caching Layer (ElastiCache)** ⚠️ MEDIUM PRIORITY
**Diagram Shows:**
- RestaurantFinderAgent → ElastiCache
- ElastiCache → Restaurant Cache

**Current State:**
- ❌ No ElastiCache integration
- ❌ No caching logic in RestaurantFinderAgent
- ❌ No cache invalidation strategy

**Impact:**
- Repeated searches hit database every time
- Higher latency for common queries
- Increased costs

**Required Implementation:**
```python
# src/utils/cache.py
import redis
import json

class RestaurantCache:
    def __init__(self):
        self.redis = redis.Redis(host=os.getenv('ELASTICACHE_ENDPOINT'))
    
    def get(self, cache_key: str):
        data = self.redis.get(cache_key)
        return json.loads(data) if data else None
    
    def set(self, cache_key: str, data: dict, ttl: int = 3600):
        self.redis.setex(cache_key, ttl, json.dumps(data))
```

---

### 4. **API Gateway + WAF** ⚠️ MEDIUM PRIORITY
**Diagram Shows:**
- Streamlit Frontend → API Gateway
- API Gateway → WAF
- API Gateway → Cognito Authorizer

**Current State:**
- ❌ No API Gateway configuration
- ❌ No WAF rules
- ✅ Cognito exists but direct integration (not via API Gateway)
- ❌ Frontend calls Lambda directly (not production-ready)

**Impact:**
- No rate limiting
- No DDoS protection
- No request throttling
- Direct Lambda exposure

**Required Implementation:**
- Deploy API Gateway REST API
- Configure WAF with rules (SQL injection, XSS, rate limiting)
- Add Cognito Authorizer to API Gateway
- Update frontend to call API Gateway endpoints

---

### 5. **User Tier / User Group Validator** ⚠️ LOW PRIORITY
**Diagram Shows:**
- Cognito User Pool → User Tier
- Cognito Authorizer → User Group Validator

**Current State:**
- ❌ No user tier logic (free, premium, enterprise)
- ❌ No group-based access control
- ❌ No tier-based feature gating

**Impact:**
- All users have same access
- No monetization strategy
- No premium features

**Required Implementation:**
```python
# src/security/user_tier.py
class UserTierValidator:
    TIERS = {
        "free": {"max_bookings_per_month": 3},
        "premium": {"max_bookings_per_month": 20},
        "enterprise": {"max_bookings_per_month": -1}  # Unlimited
    }
    
    def validate_access(self, user_id: str, feature: str):
        tier = self._get_user_tier(user_id)
        # Check tier permissions
```

---

### 6. **DynamoDB Bookings Table** ⚠️ MEDIUM PRIORITY
**Diagram Shows:**
- SAGA Workflow → DynamoDB Bookings
- DynamoDB Bookings → CloudWatch Metrics

**Current State:**
- ❌ No explicit DynamoDB table for bookings
- ❌ Bookings stored in Lambda (not persistent)
- ❌ No CloudWatch metrics on booking table

**Impact:**
- Bookings not persisted
- No booking history retrieval
- No analytics on booking patterns

**Required Implementation:**
```yaml
# template.yaml
BookingsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: RestaurantBookings
    AttributeDefinitions:
      - AttributeName: bookingId
        AttributeType: S
      - AttributeName: userId
        AttributeType: S
    KeySchema:
      - AttributeName: bookingId
        KeyType: HASH
    GlobalSecondaryIndexes:
      - IndexName: UserIdIndex
        KeySchema:
          - AttributeName: userId
            KeyType: HASH
```

---

### 7. **Weather Intelligence Components** ⚠️ HIGH PRIORITY
**Diagram Shows:**
- Weather Analysis [icon: brain]
- Bad Weather Detection [icon: alert]
- Forecast Range Calculator [icon: calendar]

**Current State:**
- ❌ No weather analysis logic
- ❌ No bad weather detection algorithm
- ❌ No forecast range calculation

**Required Implementation:**
```python
# src/agents/weather_agent.py
class WeatherAnalyzer:
    BAD_WEATHER_CONDITIONS = ["rain", "snow", "thunderstorm"]
    EXTREME_TEMP_THRESHOLD = {"low": 32, "high": 95}
    
    def analyze(self, weather_data: dict) -> dict:
        is_bad = self._detect_bad_weather(weather_data)
        forecast_range = self._calculate_forecast_range(weather_data) if is_bad else None
        return {"is_bad_weather": is_bad, "forecast_range": forecast_range}
    
    def _detect_bad_weather(self, data: dict) -> bool:
        condition = data.get("condition", "").lower()
        temp = data.get("temperature", 70)
        return (
            any(bad in condition for bad in self.BAD_WEATHER_CONDITIONS) or
            temp < self.EXTREME_TEMP_THRESHOLD["low"] or
            temp > self.EXTREME_TEMP_THRESHOLD["high"]
        )
    
    def _calculate_forecast_range(self, data: dict) -> dict:
        # Find next good weather day within 7 days
        pass
```

---

### 8. **Workflow Steps (Detailed Flow)** ⚠️ LOW PRIORITY
**Diagram Shows:**
- Step 1: Intent Classification
- Step 2A: Search Flow (Steps 3-7)
- Step 2B: Booking Flow (Steps 3B-8B)
- Step 2C: History Flow (Steps 3C-4C)

**Current State:**
- ✅ Basic flows implemented
- ❌ No explicit step tracking
- ❌ No step-level observability
- ❌ No history flow implementation

**Impact:**
- Hard to debug multi-step flows
- No visibility into where failures occur
- Missing booking history feature

---

## 📊 PRIORITY MATRIX

| Component | Priority | Effort | Impact | Status |
|-----------|----------|--------|--------|--------|
| AgentCore Gateway Integration | MEDIUM | Low | High | ⚠️ Deployed but bypassed |
| Cognito User Tier Validation | MEDIUM | Low | Medium | ⚠️ Configured but unused |
| WeatherAgent | HIGH | Medium | High | ❌ Missing |
| Weather MCP Tools | HIGH | Low | High | ❌ Missing |
| Weather Intelligence | HIGH | Medium | High | ❌ Missing |
| DynamoDB Bookings | MEDIUM | Low | Medium | ❌ Missing |
| ElastiCache | MEDIUM | Medium | Medium | ❌ Missing |
| API Gateway + WAF | MEDIUM | Medium | High | ❌ Missing |
| History Flow | LOW | Low | Medium | ❌ Missing |
| Step Tracking | LOW | Low | Low | ❌ Missing |

---

## 🎯 RECOMMENDED IMPLEMENTATION ORDER

### Phase 0: Fix Gateway & Cognito Integration (Week 0 - Quick Wins)
1. **Update MCPToolClient to use Gateway** (2 hours)
   - Modify `src/tools/mcp_client.py` to call Gateway URL instead of Lambda
   - Add JWT token retrieval from Cognito
   - Pass Authorization header with Bearer token
   - Test all 8 tools through Gateway

2. **Implement User Tier Validation** (4 hours)
   - Create `src/security/user_tier.py` with `UserTierValidator`
   - Add tier extraction from JWT in workflow
   - Implement booking limit checks
   - Add tier-based feature gating

3. **Frontend JWT Authentication** (3 hours)
   - Add login form to Streamlit app
   - Store JWT token in session state
   - Extract and display user tier
   - Pass tier to orchestrator

### Phase 1: Weather Intelligence (Week 1)
1. Create `WeatherAgent` class
2. Implement weather MCP tools (weatherAPI, forecastAPI)
3. Add weather analysis logic
4. Integrate into LangGraph workflow
5. Add weather node between restaurant_finder and booking_agent

### Phase 2: Data Persistence (Week 2)
1. Create DynamoDB Bookings table
2. Update booking tools to persist to DynamoDB
3. Add booking history retrieval
4. Implement history flow in workflow

### Phase 3: Performance & Security (Week 3)
1. Deploy ElastiCache cluster
2. Add caching to RestaurantFinderAgent
3. Deploy API Gateway
4. Configure WAF rules
5. Update frontend to use API Gateway

### Phase 4: Advanced Features (Week 4)
1. Implement user tier logic
2. Add step-level tracking
3. Enhanced observability
4. Performance optimization

---

## 📝 NOTES

### Strengths of Current Implementation
- ✅ Solid SOLID principles adherence
- ✅ Clean separation of concerns (Strands + LangGraph)
- ✅ Cost optimization with model router
- ✅ SAGA pattern for transaction safety
- ✅ Security with prompt injection defense
- ✅ Memory integration for conversation persistence
- ✅ AgentCore Gateway deployed and configured
- ✅ Cognito User Pool with custom tier attribute

### Architecture Alignment
- **85% aligned** with core architecture
- **Missing 15%**: Weather intelligence (10%), Gateway integration (3%), Tier validation (2%)

### Critical Finding: "Deployed but Not Used"
🚨 **AgentCore Gateway and Cognito are fully deployed but completely bypassed in the application flow:**
- Gateway exists with all tools registered
- Cognito has user tiers configured
- BUT: Code calls Lambda directly, ignoring Gateway
- BUT: Tier attribute exists but never validated

This is a **quick win** - infrastructure is ready, just needs code integration.

### Technical Debt
- Gateway bypass in MCPToolClient (HIGH priority fix)
- Unused Cognito tier attribute (MEDIUM priority)
- No integration tests for weather flow
- No load testing for ElastiCache
- No WAF rule validation
- No user tier enforcement

---

## 🔗 RELATED DOCUMENTS
- `architecture-diagram.eraser` - Visual architecture
- `project-rules.md` - Implementation guidelines
- `application-prod.md` - Production patterns
- `IMPLEMENTATION_PLAN.md` - Detailed tasks
