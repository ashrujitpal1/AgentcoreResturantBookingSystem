# Tool Design Principles Compliance Audit

## Audit Summary

**Status:** ⚠️ PARTIAL COMPLIANCE - 4 violations found

---

## Principle 1: Idempotency ⚠️

**Rule:** All tools accept requestId for deduplication

### ✅ COMPLIANT (3 tools)
- `registerUser` - ✅ Requires requestId, implements idempotency caching
- `bookATable` - ✅ Requires requestId, implements idempotency caching
- `paymentAPI` - ✅ Requires requestId, implements idempotency caching

### ❌ NON-COMPLIANT (4 tools)
- `fetchRestaurantDetails` - ❌ No requestId parameter
- `fetchRestaurantDetailsById` - ❌ No requestId parameter
- `searchUserDetails` - ❌ No requestId parameter
- `tokenAmountCalculation` - ❌ No requestId parameter

**Violation Details:**
```python
# fetch_restaurant_details.py - NO requestId
def lambda_handler(event, context):
    city = event.get('city')
    cuisine = event.get('cuisine')
    # No requestId handling
```

**Impact:** READ_ONLY tools can be called multiple times without deduplication, potentially causing:
- Unnecessary DynamoDB read costs
- Inconsistent results if data changes between calls
- No audit trail for repeated queries

**Recommendation:** Add optional requestId to READ_ONLY tools for observability and caching

---

## Principle 2: Side-Effect Classification ✅

**Rule:** READ_ONLY | MUTATING | IRREVERSIBLE

### Classification Status: ✅ CORRECT

| Tool | Classification | Correct? | Evidence |
|------|----------------|----------|----------|
| fetchRestaurantDetails | READ_ONLY | ✅ | Only queries DynamoDB |
| fetchRestaurantDetailsById | READ_ONLY | ✅ | Only queries DynamoDB |
| searchUserDetails | READ_ONLY | ✅ | Only queries DynamoDB |
| tokenAmountCalculation | READ_ONLY | ✅ | Pure calculation, no DB writes |
| registerUser | MUTATING | ✅ | Creates user record, reversible |
| bookATable | IRREVERSIBLE | ✅ | Creates booking, requires compensation |
| paymentAPI | IRREVERSIBLE | ✅ | Processes payment, requires refund |

**Status:** ✅ All tools correctly classified

---

## Principle 3: Bounded Execution ⚠️

**Rule:** Max 30s timeout, output size limits

### Timeout Configuration: ❌ NOT ENFORCED IN CODE

**Current State:**
- Lambda timeout configured in SAM template (likely 30s)
- No explicit timeout handling in Lambda code
- No graceful degradation for long-running queries

**Missing Implementation:**
```python
# fetch_restaurant_details.py - No timeout handling
response = table.scan()  # Could take >30s on large tables
```

**Violation:** `fetchRestaurantDetails` uses `table.scan()` without pagination limits

### Output Size Limits: ⚠️ PARTIAL

**Implemented:**
```python
# fetch_restaurant_details.py
MAX_RESULTS = 50  # ✅ Limits output size
restaurants = restaurants[:MAX_RESULTS]
```

**Missing:**
- No size limit on individual restaurant objects (menuCard could be huge)
- No total payload size check (50 restaurants * large objects = potential Lambda limit breach)
- No truncation strategy for large descriptions

**Recommendation:**
1. Add pagination support for large result sets
2. Implement payload size monitoring
3. Add field truncation for large text fields

---

## Principle 4: Deterministic Behavior ⚠️

**Rule:** Same input → same output

### ✅ DETERMINISTIC (5 tools)
- `fetchRestaurantDetailsById` - ✅ Same restaurantId → same restaurant
- `tokenAmountCalculation` - ✅ Pure function, no randomness
- `registerUser` - ✅ Idempotent with requestId
- `bookATable` - ✅ Idempotent with requestId
- `paymentAPI` - ✅ Uses deterministic_hash() for simulation

### ❌ NON-DETERMINISTIC (2 tools)
- `fetchRestaurantDetails` - ❌ Results change if data is modified
- `searchUserDetails` - ❌ Results change if user data is modified

**Violation Details:**
```python
# fetch_restaurant_details.py
# Query results depend on current DB state
response = table.query(IndexName='CityIndex', KeyConditionExpression=Key('city').eq(city))
# If restaurants are added/removed, same query returns different results
```

**Impact:**
- Agent may get different results for same query in same conversation
- Difficult to reproduce issues
- Testing becomes non-deterministic

**Recommendation:**
- Add timestamp-based versioning for READ_ONLY queries
- Implement result caching with TTL
- Add `asOfTime` parameter for point-in-time queries

---

## Principle 5: Schema-First Validation ✅

**Rule:** Strict input/output validation

### ✅ COMPLIANT (All 7 tools)

**Input Validation:**
```python
# registerUser.py - ✅ Strict validation
if not all([username, mobile_no, user_city]):
    return {'error': 'username, mobileNo, and userCity are required'}

is_valid, error = validate_phone(mobile_no)
if not is_valid:
    return {'error': f'Invalid mobileNo: {error}'}
```

**Validation Functions:**
- `validate_phone()` - ✅ Phone number format validation
- `validate_guests()` - ✅ Guest count range validation (1-20)
- `validate_amount()` - ✅ Token amount validation (positive, max limit)
- `validate_schema()` - ✅ Generic schema validation with custom validators

**Output Validation:**
- All tools return consistent error format: `{'error': 'message'}`
- Success responses follow documented schemas
- Type consistency maintained (Decimal → float conversion)

**Status:** ✅ All tools implement strict validation

---

## Compliance Score

| Principle | Status | Score |
|-----------|--------|-------|
| 1. Idempotency | ⚠️ Partial | 3/7 (43%) |
| 2. Side-Effect Classification | ✅ Full | 7/7 (100%) |
| 3. Bounded Execution | ⚠️ Partial | 1/2 (50%) |
| 4. Deterministic Behavior | ⚠️ Partial | 5/7 (71%) |
| 5. Schema-First Validation | ✅ Full | 7/7 (100%) |

**Overall Compliance:** 72% (23/30 points)

---

## Critical Violations

### 🔴 HIGH PRIORITY

1. **Missing requestId on READ_ONLY tools**
   - **Impact:** No observability, no caching, no audit trail
   - **Fix:** Add optional requestId parameter to all 4 READ_ONLY tools
   - **Effort:** Low (1-2 hours)

2. **Unbounded table.scan() in fetchRestaurantDetails**
   - **Impact:** Potential timeout on large datasets
   - **Fix:** Add pagination with LastEvaluatedKey
   - **Effort:** Medium (2-4 hours)

### 🟡 MEDIUM PRIORITY

3. **Non-deterministic READ_ONLY queries**
   - **Impact:** Inconsistent agent behavior
   - **Fix:** Implement result caching with 5-minute TTL
   - **Effort:** Medium (3-5 hours)

4. **No output size limits on individual objects**
   - **Impact:** Potential Lambda payload limit breach
   - **Fix:** Add field truncation for large text fields
   - **Effort:** Low (1-2 hours)

---

## Recommended Fixes

### Fix 1: Add requestId to READ_ONLY tools

```python
# fetch_restaurant_details.py
def lambda_handler(event, context):
    request_id = event.get('requestId')  # Optional for READ_ONLY
    
    # Check cache if requestId provided
    if request_id:
        cached = check_cache(request_id, ttl=300)  # 5-minute cache
        if cached:
            return cached
    
    # ... existing logic ...
    
    result = {'restaurants': [dict(r) for r in restaurants]}
    
    # Store in cache if requestId provided
    if request_id:
        store_cache(request_id, result, ttl=300)
    
    return result
```

### Fix 2: Add pagination to fetchRestaurantDetails

```python
# fetch_restaurant_details.py
def lambda_handler(event, context):
    max_results = min(int(event.get('maxResults', 50)), 100)
    next_token = event.get('nextToken')
    
    scan_kwargs = {'Limit': max_results}
    if next_token:
        scan_kwargs['ExclusiveStartKey'] = json.loads(base64.b64decode(next_token))
    
    response = table.scan(**scan_kwargs)
    
    result = {'restaurants': response['Items']}
    if 'LastEvaluatedKey' in response:
        result['nextToken'] = base64.b64encode(json.dumps(response['LastEvaluatedKey']))
    
    return result
```

### Fix 3: Add output size limits

```python
# fetch_restaurant_details.py
MAX_DESCRIPTION_LENGTH = 500
MAX_MENU_ITEMS = 10

def truncate_restaurant(restaurant):
    if 'description' in restaurant and len(restaurant['description']) > MAX_DESCRIPTION_LENGTH:
        restaurant['description'] = restaurant['description'][:MAX_DESCRIPTION_LENGTH] + '...'
    
    if 'menuCard' in restaurant and len(restaurant['menuCard']) > MAX_MENU_ITEMS:
        restaurant['menuCard'] = restaurant['menuCard'][:MAX_MENU_ITEMS]
    
    return restaurant

# In lambda_handler
restaurants = [truncate_restaurant(r) for r in restaurants]
```

---

## Conclusion

**Current State:** Tools are production-ready for MUTATING/IRREVERSIBLE operations (registerUser, bookATable, paymentAPI) with proper idempotency and validation.

**Gaps:** READ_ONLY tools lack observability (no requestId) and bounded execution guarantees (unbounded scan).

**Recommendation:** Implement HIGH PRIORITY fixes before agent deployment to ensure:
- Consistent agent behavior with result caching
- Protection against timeout failures
- Complete audit trail for all tool invocations

**Timeline:** 4-6 hours to achieve 100% compliance
