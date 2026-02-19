# Task List: Cognito Authentication & Authorization for Weather API

## 📋 Overview

Implement JWT-based authentication using AWS Cognito with role-based access control (RBAC) for the Weather Mock Service.

**Access Control:**
- **Normal Users:** Access to `/weather` endpoint only
- **Gold Users:** Access to both `/weather` and `/forecast` endpoints
- **Public:** `/health` endpoint (no authentication required)

---

## Phase 1: Cognito User Pool Configuration

### ✅ Task 1.1: Add Custom Attribute to Existing User Pool

**Objective:** Add a custom attribute to store user tier information

**Automated Approach (Recommended):**

```bash
cd mock-weather-service
python3 update_cognito_for_weather.py us-east-1_v7ilQRXCR us-east-1
```

**Note:** Custom attributes cannot be added to existing user pools via API. If the script reports the attribute is missing, follow the manual steps below.

**Manual Steps (if needed):**
1. Open AWS Console → Cognito → User Pools
2. Select User Pool: `us-east-1_v7ilQRXCR`
3. Navigate to "Sign-up experience" → "Custom attributes"
4. Click "Add custom attribute"
5. Configure:
   - Name: `tier`
   - Type: `String`
   - Min length: 4
   - Max length: 10
   - Mutable: Yes (allow tier upgrades)
6. Save changes
7. Re-run the script: `python3 update_cognito_for_weather.py`

**Verification:**
```bash
aws cognito-idp describe-user-pool \
  --user-pool-id us-east-1_v7ilQRXCR \
  --query 'UserPool.SchemaAttributes[?Name==`custom:tier`]'
```

**Expected Output:** Custom attribute `custom:tier` exists

---

### ✅ Task 1.2: Create Test Users

**Objective:** Create test users with different tier levels

**Automated Approach (Recommended):**

The `update_cognito_for_weather.py` script automatically creates both users:

```bash
cd mock-weather-service
python3 update_cognito_for_weather.py us-east-1_v7ilQRXCR us-east-1
```

**Created Users:**
- **normal_user** (tier: normal, password: WeatherTest123!)
- **gold_user** (tier: gold, password: WeatherTest123!)

**Manual Approach (if needed):**

**Normal User:**
```bash
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_v7ilQRXCR \
  --username normal_user \
  --user-attributes Name=email,Value=normal@example.com Name=custom:tier,Value=normal \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_v7ilQRXCR \
  --username normal_user \
  --password "WeatherTest123!" \
  --permanent
```

**Gold User:**
```bash
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_v7ilQRXCR \
  --username gold_user \
  --user-attributes Name=email,Value=gold@example.com Name=custom:tier,Value=gold \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_v7ilQRXCR \
  --username gold_user \
  --password "WeatherTest123!" \
  --permanent
```

**Verification:**
```bash
# List users
aws cognito-idp list-users --user-pool-id us-east-1_v7ilQRXCR

# Check specific user
aws cognito-idp admin-get-user \
  --user-pool-id us-east-1_v7ilQRXCR \
  --username normal_user
```

---

### ✅ Task 1.3: Verify Cognito Configuration

**Objective:** Test user login and verify JWT token structure

**Automated Verification:**

The `update_cognito_for_weather.py` script automatically verifies:
- Custom attribute exists
- Users created successfully
- Users have correct tier attributes
- Login works and returns JWT tokens

**Manual Verification (if needed):**

**Get Client ID:**
```bash
aws cognito-idp list-user-pool-clients \
  --user-pool-id us-east-1_v7ilQRXCR
```

**Test Login (Normal User):**
```bash
aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_v7ilQRXCR \
  --client-id <CLIENT_ID> \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=normal_user,PASSWORD=WeatherTest123!
```

**Decode JWT Token:**
```bash
# Copy AccessToken from response
# Decode at https://jwt.io or use:
echo "<ACCESS_TOKEN>" | cut -d'.' -f2 | base64 -d | jq
```

**Expected Claims:**
- `username`: `normal_user`
- `custom:tier`: `normal`
- `exp`: Expiration timestamp
- `iss`: Cognito issuer URL

**Deliverables:**
- [ ] Custom attribute `custom:tier` created
- [ ] 2 test users created (normal_user, gold_user)
- [ ] JWT tokens contain `custom:tier` claim
- [ ] Document Client ID: `_________________`

---

## Phase 2: Flask Application - Authentication Module

### ✅ Task 2.1: Update Dependencies

**Objective:** Add required libraries for JWT verification

**File:** `mock-weather-service/requirements.txt`

**Add:**
```
Flask==3.0.0
gunicorn==21.2.0
python-jose[cryptography]==3.3.0
requests==2.31.0
```

**Install:**
```bash
cd mock-weather-service
pip install -r requirements.txt
```

**Verification:**
```bash
python -c "from jose import jwt; print('JWT library installed')"
```

**Deliverables:**
- [ ] requirements.txt updated
- [ ] Dependencies installed successfully

---

### ✅ Task 2.2: Create `auth.py` - JWT Verification

**Objective:** Implement Cognito JWT token verification

**File:** `mock-weather-service/auth.py`

**Functions to Implement:**

1. **`get_cognito_public_keys()`**
   - Download JWKS from Cognito
   - Cache keys for 24 hours
   - Return: Dict of public keys

2. **`verify_jwt_token(token)`**
   - Verify JWT signature using public keys
   - Check token expiration
   - Validate issuer and audience
   - Return: Decoded token claims or raise exception

3. **`extract_user_info(token)`**
   - Extract username from token
   - Extract `custom:tier` attribute
   - Return: `{"username": str, "tier": str}`

**Configuration:**
```python
USER_POOL_ID = "us-east-1_v7ilQRXCR"
REGION = "us-east-1"
JWKS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
```

**Error Handling:**
- `TokenExpiredError`: Token has expired
- `InvalidSignatureError`: Invalid token signature
- `InvalidTokenError`: Malformed token
- `MissingClaimError`: Required claim not found

**Deliverables:**
- [ ] auth.py created (~80 lines)
- [ ] All 3 functions implemented
- [ ] Error handling added
- [ ] Public key caching implemented

---

### ✅ Task 2.3: Create `middleware.py` - Authorization Decorator

**Objective:** Create Flask decorator for endpoint protection

**File:** `mock-weather-service/middleware.py`

**Decorator to Implement:**

```python
def require_auth(tier="normal"):
    """
    Decorator to protect endpoints with authentication and authorization
    
    Args:
        tier: Minimum tier required ("normal" or "gold")
    
    Returns:
        Decorated function with auth checks
    """
```

**Logic Flow:**
1. Extract `Authorization: Bearer <token>` from request headers
2. If missing → Return 401 Unauthorized
3. Call `verify_jwt_token(token)`
4. If invalid → Return 401 Unauthorized
5. Call `extract_user_info(token)`
6. Check if user tier >= required tier
   - normal user + gold endpoint → Return 403 Forbidden
   - gold user + any endpoint → Allow
   - normal user + normal endpoint → Allow
7. Attach user info to `request.user` for logging
8. Call original endpoint function

**Error Responses:**
```json
// 401 Unauthorized
{
  "error": "Missing or invalid authentication token",
  "code": "UNAUTHORIZED"
}

// 403 Forbidden
{
  "error": "Gold tier required for this endpoint",
  "code": "FORBIDDEN",
  "required_tier": "gold",
  "user_tier": "normal"
}
```

**Deliverables:**
- [ ] middleware.py created (~40 lines)
- [ ] `@require_auth()` decorator implemented
- [ ] Tier hierarchy logic correct
- [ ] Error responses standardized

---

## Phase 3: Flask Application - Endpoint Protection

### ✅ Task 3.1: Update `app.py` - Add Authentication

**Objective:** Protect endpoints with authentication decorators

**File:** `mock-weather-service/app.py`

**Changes:**

1. **Add imports:**
```python
import os
from auth import verify_jwt_token, extract_user_info
from middleware import require_auth
```

2. **Add configuration:**
```python
# After app initialization
USER_POOL_ID = os.getenv('USER_POOL_ID', 'us-east-1_v7ilQRXCR')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
```

3. **Protect endpoints:**
```python
# /health - Keep public (no decorator)

@app.route('/weather', methods=['GET'])
@require_auth(tier="normal")  # ADD THIS LINE
def get_weather():
    # existing code...

@app.route('/forecast', methods=['GET'])
@require_auth(tier="gold")  # ADD THIS LINE
def get_forecast():
    # existing code...
```

**Deliverables:**
- [ ] app.py updated with imports
- [ ] Environment variables added
- [ ] `/weather` protected with `@require_auth("normal")`
- [ ] `/forecast` protected with `@require_auth("gold")`
- [ ] `/health` remains public

---

### ✅ Task 3.2: Add Error Handling & Logging

**Objective:** Improve observability and debugging

**File:** `mock-weather-service/app.py`

**Add:**

1. **Logging configuration:**
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

2. **Request logging middleware:**
```python
@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path} - User: {getattr(request, 'user', 'anonymous')}")
```

3. **Error handlers:**
```python
@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized", "message": str(error)}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({"error": "Forbidden", "message": str(error)}), 403
```

**Deliverables:**
- [ ] Logging configured
- [ ] Request logging added
- [ ] Error handlers implemented

---

## Phase 4: Testing

### ✅ Task 4.1: Unit Tests

**Objective:** Test authentication functions in isolation

**File:** `mock-weather-service/test_auth_unit.py`

**Tests to Implement:**

1. **test_verify_valid_token()**
   - Create valid JWT token
   - Verify it passes validation
   - Assert claims are correct

2. **test_verify_expired_token()**
   - Create expired JWT token
   - Verify it raises TokenExpiredError

3. **test_verify_invalid_signature()**
   - Create token with wrong signature
   - Verify it raises InvalidSignatureError

4. **test_extract_user_info_normal()**
   - Token with `custom:tier = "normal"`
   - Assert tier extracted correctly

5. **test_extract_user_info_gold()**
   - Token with `custom:tier = "gold"`
   - Assert tier extracted correctly

**Run:**
```bash
python -m pytest test_auth_unit.py -v
```

**Deliverables:**
- [ ] test_auth_unit.py created
- [ ] 5 unit tests implemented
- [ ] All tests pass

---

### ✅ Task 4.2: Integration Tests - Normal User

**Objective:** Test API access for normal tier users

**File:** `mock-weather-service/test_integration_normal.py`

**Prerequisites:**
- Flask app running on localhost:8080
- Normal user credentials available

**Tests:**

1. **test_normal_user_login()**
   - Login as normal_user
   - Assert access token received
   - Assert token contains `custom:tier = "normal"`

2. **test_normal_user_weather_access()**
   - Call `/weather` with normal user token
   - Assert 200 OK response
   - Assert weather data returned

3. **test_normal_user_forecast_denied()**
   - Call `/forecast` with normal user token
   - Assert 403 Forbidden response
   - Assert error message mentions "Gold tier required"

4. **test_no_token_denied()**
   - Call `/weather` without token
   - Assert 401 Unauthorized response

**Run:**
```bash
python test_integration_normal.py
```

**Deliverables:**
- [ ] test_integration_normal.py created
- [ ] 4 integration tests implemented
- [ ] All tests pass

---

### ✅ Task 4.3: Integration Tests - Gold User

**Objective:** Test API access for gold tier users

**File:** `mock-weather-service/test_integration_gold.py`

**Tests:**

1. **test_gold_user_login()**
   - Login as gold_user
   - Assert access token received
   - Assert token contains `custom:tier = "gold"`

2. **test_gold_user_weather_access()**
   - Call `/weather` with gold user token
   - Assert 200 OK response

3. **test_gold_user_forecast_access()**
   - Call `/forecast` with gold user token
   - Assert 200 OK response
   - Assert 7-day forecast returned

4. **test_gold_user_full_access()**
   - Call both endpoints with gold token
   - Assert both succeed

**Run:**
```bash
python test_integration_gold.py
```

**Deliverables:**
- [ ] test_integration_gold.py created
- [ ] 4 integration tests implemented
- [ ] All tests pass

---

### ✅ Task 4.4: Create Automated Test Script

**Objective:** Single script to run all tests

**File:** `mock-weather-service/run_all_tests.sh`

**Script:**
```bash
#!/bin/bash
set -e

echo "🧪 Running Authentication Tests"
echo "================================"

echo "1. Unit Tests..."
python -m pytest test_auth_unit.py -v

echo "2. Integration Tests - Normal User..."
python test_integration_normal.py

echo "3. Integration Tests - Gold User..."
python test_integration_gold.py

echo "================================"
echo "✅ All tests passed!"
```

**Run:**
```bash
chmod +x run_all_tests.sh
./run_all_tests.sh
```

**Deliverables:**
- [ ] run_all_tests.sh created
- [ ] Script runs all tests
- [ ] Test report generated

---

## Phase 5: Documentation & Deployment

### ✅ Task 5.1: Create Authentication Setup Guide

**Objective:** Document setup process

**File:** `mock-weather-service/AUTH_SETUP.md`

**Sections:**
1. Prerequisites
2. Cognito Configuration
3. User Creation
4. Testing Authentication
5. Troubleshooting

**Deliverables:**
- [ ] AUTH_SETUP.md created
- [ ] All setup steps documented
- [ ] Examples included

---

### ✅ Task 5.2: Create API Usage Guide

**Objective:** Document how to use authenticated APIs

**File:** `mock-weather-service/API_AUTH_GUIDE.md`

**Sections:**
1. Getting Access Token
2. Making Authenticated Requests
3. Error Codes
4. Tier Comparison Table
5. Code Examples (curl, Python, JavaScript)

**Example:**
```bash
# 1. Login
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_v7ilQRXCR \
  --client-id <CLIENT_ID> \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=gold_user,PASSWORD=WeatherTest123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text)

# 2. Call API
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/forecast?city=Miami&date=2026-02-10"
```

**Deliverables:**
- [ ] API_AUTH_GUIDE.md created
- [ ] All endpoints documented
- [ ] Examples for both tiers

---

### ✅ Task 5.3: Update Existing Documentation

**Objective:** Update all docs with authentication info

**Files to Update:**

1. **README.md**
   - Add "Authentication" section
   - Link to AUTH_SETUP.md and API_AUTH_GUIDE.md
   - Update API examples with tokens

2. **QUICKSTART.md**
   - Add login step before API calls
   - Update curl examples

3. **FORECAST_UPDATE.md**
   - Add authentication requirements
   - Update examples

**Deliverables:**
- [ ] README.md updated
- [ ] QUICKSTART.md updated
- [ ] FORECAST_UPDATE.md updated

---

### ✅ Task 5.4: EC2 Deployment Configuration

**Objective:** Configure EC2 for authenticated service

**File:** `mock-weather-service/deploy_ec2_auth.sh`

**Script:**
```bash
#!/bin/bash
# Deploy authenticated weather service to EC2

# Set environment variables
export USER_POOL_ID=us-east-1_v7ilQRXCR
export AWS_REGION=us-east-1

# Install dependencies
pip3 install -r requirements.txt

# Create systemd service with env vars
sudo tee /etc/systemd/system/weather-mock.service > /dev/null <<EOF
[Unit]
Description=Mock Weather Service with Auth
After=network.target

[Service]
User=ec2-user
WorkingDirectory=$(pwd)
Environment="USER_POOL_ID=us-east-1_v7ilQRXCR"
Environment="AWS_REGION=us-east-1"
ExecStart=/usr/local/bin/gunicorn -w 2 -b 0.0.0.0:8080 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable weather-mock
sudo systemctl restart weather-mock

echo "✅ Authenticated service deployed!"
```

**Deliverables:**
- [ ] deploy_ec2_auth.sh created
- [ ] Environment variables configured
- [ ] Service deployed successfully

---

## Phase 6: AgentCore Gateway Integration (Optional)

### ✅ Task 6.1: Configure Gateway for Token Pass-Through

**Objective:** Enable gateway to forward Authorization headers

**File:** `mock-weather-service/register_with_gateway.py`

**Implementation:**
```python
import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Register weather endpoint
bedrock_agent.create_agent_action_group(
    agentId='<AGENT_ID>',
    actionGroupName='WeatherTools',
    actionGroupExecutor={
        'customControl': 'RETURN_CONTROL'
    },
    apiSchema={
        'payload': json.dumps({
            'openapi': '3.0.0',
            'paths': {
                '/weather': {
                    'get': {
                        'security': [{'BearerAuth': []}],
                        'parameters': [...]
                    }
                }
            },
            'components': {
                'securitySchemes': {
                    'BearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer'
                    }
                }
            }
        })
    }
)
```

**Deliverables:**
- [ ] Gateway configured for auth headers
- [ ] Tools registered with security scheme
- [ ] Test gateway → EC2 flow

---

### ✅ Task 6.2: Agent Token Management

**Objective:** Enable agents to obtain and use tokens

**Considerations:**
- Create service account in Cognito for agents
- Implement token refresh logic
- Cache tokens to avoid repeated logins
- Handle token expiration gracefully

**Deliverables:**
- [ ] Service account created
- [ ] Token management implemented
- [ ] Documentation updated

---

## 📊 Progress Tracking

| Phase | Tasks | Status | Completion |
|-------|-------|--------|------------|
| 1. Cognito Setup | 3 | ⬜ Not Started | 0% |
| 2. Auth Module | 3 | ⬜ Not Started | 0% |
| 3. Endpoint Protection | 2 | ⬜ Not Started | 0% |
| 4. Testing | 4 | ⬜ Not Started | 0% |
| 5. Documentation | 4 | ⬜ Not Started | 0% |
| 6. Gateway Integration | 2 | ⬜ Not Started | 0% |
| **TOTAL** | **18** | **⬜** | **0%** |

**Legend:**
- ⬜ Not Started
- 🟡 In Progress
- ✅ Completed

---

## 🎯 Acceptance Criteria

- [ ] Normal users can access `/weather` only
- [ ] Gold users can access both `/weather` and `/forecast`
- [ ] Unauthenticated requests return 401
- [ ] Unauthorized requests return 403
- [ ] JWT tokens are properly validated
- [ ] User tier is correctly extracted from Cognito
- [ ] All unit tests pass (5/5)
- [ ] All integration tests pass (8/8)
- [ ] Documentation is complete and accurate
- [ ] Service deployed to EC2 with authentication
- [ ] AgentCore Gateway integration tested (optional)

---

## 📝 Notes

- Estimated total implementation time: 4-6 hours
- Estimated lines of code: ~230 lines
- Dependencies: python-jose, requests
- AWS services: Cognito User Pool (existing)
- No Lambda functions required (direct HTTP)

---

## 🚀 Quick Start

```bash
# 1. Complete Phase 1 (Cognito setup)
# 2. Install dependencies
cd mock-weather-service
pip install -r requirements.txt

# 3. Create auth modules
# (Implement auth.py and middleware.py)

# 4. Update app.py
# (Add decorators)

# 5. Run tests
./run_all_tests.sh

# 6. Deploy to EC2
./deploy_ec2_auth.sh
```

---

**Ready to start implementation? Begin with Phase 2 (Auth Module).**
