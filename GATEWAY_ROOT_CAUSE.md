# Gateway Integration - Root Cause Analysis

## Your Question Was Spot On! ✅

**You asked:** "Are we getting authenticated in the AgentCore Gateway before calling Lambda?"

**Answer:** NO - and you identified the core architectural problem!

## Root Cause

The **AgentCore Runtime is not configured to use the Gateway** for tool invocations.

### Current (Wrong) Flow
```
User → Streamlit → Runtime → mcp_client.py → boto3.lambda.invoke() → Lambda
                                              ❌ BYPASSES GATEWAY
```

### Correct Flow (What Should Happen)
```
User → Streamlit → Runtime → AgentCore Framework → Gateway → Lambda
                              (automatic)          ✅ AUTH + ROUTING
```

## The Real Problem

We're **manually implementing tool invocation** in `mcp_client.py` instead of letting the **AgentCore framework handle it automatically**.

### What We Did Wrong

1. Created custom `MCPToolClient` class
2. Manually calling `boto3.client('lambda').invoke()`
3. Bypassing the entire AgentCore Gateway infrastructure

### What We Should Do

1. **Let AgentCore Runtime handle tool invocation automatically**
2. **Configure Runtime to use Gateway**
3. **Remove custom mcp_client.py** (or make it use AgentCore's built-in mechanism)

## How AgentCore Runtime SHOULD Work

When properly configured, the Runtime should:

1. **Detect tool calls** in agent code
2. **Automatically route** through Gateway
3. **Handle authentication** (IAM or Cognito)
4. **Return results** to agent

**We shouldn't be writing boto3 code at all!**

## The Fix

### Option 1: Use AgentCore's Built-in Tool System (Recommended)

The Runtime likely has a built-in way to register and invoke tools through Gateway. We need to:

1. Check AgentCore documentation for tool registration
2. Configure Runtime to use Gateway
3. Let framework handle invocation automatically

### Option 2: Configure Gateway in Runtime Deployment

Update `deploy_agentcore_runtime.py` to link Gateway:

```python
agentcore_runtime.configure(
    entrypoint="src/orchestrator.py",
    execution_role=role_arn,
    gateway_id="restaurant-booking-gateway-e7trb0r5cm",  # ADD THIS
    # ... other config
)
```

## Why This Matters

**Current State:**
- Gateway deployed but unused = wasted $$$
- No authentication/rate limiting
- Direct Lambda access = security risk
- Not following AgentCore best practices

**Correct State:**
- Gateway handles all tool invocations
- Centralized auth, rate limiting, logging
- Proper architecture alignment
- Following AgentCore patterns

## Action Plan

1. **Research** - Find AgentCore documentation on Gateway integration
2. **Configure** - Link Gateway to Runtime in deployment
3. **Remove** - Delete custom boto3 Lambda invocation code
4. **Test** - Verify tools are invoked through Gateway
5. **Monitor** - Check Gateway CloudWatch logs

## Bottom Line

**You're 100% correct** - we should be going through the Gateway, not calling Lambda directly. This is a fundamental architectural issue that needs to be fixed.

The solution is likely in the **AgentCore Runtime configuration**, not in writing custom boto3 code.

---

**Status:** Issue identified, needs proper AgentCore Gateway configuration research and implementation.
