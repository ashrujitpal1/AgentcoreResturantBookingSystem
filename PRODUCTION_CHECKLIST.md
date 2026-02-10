# Production Deployment Checklist

## Pre-Deployment (Complete These First)

### Infrastructure
- [x] AgentCore Runtime deployed
- [x] AgentCore Memory configured
- [x] AgentCore Gateway registered
- [x] Lambda functions deployed
- [x] DynamoDB tables created
- [ ] **S3 prompts bucket configured**
- [ ] **CloudWatch alarms created**
- [ ] **WAF rules configured**

### Security
- [ ] **Prompt injection validation tested**
- [ ] **Rate limiting configured (100 req/min)**
- [ ] **PII redaction enabled**
- [ ] **Secrets moved to Secrets Manager**
- [ ] **IAM roles audited (least privilege)**

### Testing
- [ ] **Unit tests passing (>80% coverage)**
- [ ] **Integration tests completed**
- [ ] **Load test (target: 100 concurrent users)**
- [ ] **Security scan completed**

### Observability
- [ ] **CloudWatch dashboard created**
- [ ] **X-Ray tracing enabled**
- [ ] **Cost tracking configured**
- [ ] **Alert SNS topics configured**

## Deployment Steps

1. **Upload Prompts to S3**
   ```bash
   python3 deploy_prompts_to_s3.py
   ```

2. **Deploy Monitoring**
   ```bash
   python3 deploy_monitoring.py
   ```

3. **Run Integration Tests**
   ```bash
   python3 tests/test_complete_booking.py
   ```

4. **Update Runtime with Production Config**
   ```bash
   python3 deploy_agentcore_runtime.py --env production
   ```

5. **Enable X-Ray Tracing**
   ```bash
   aws bedrock-agentcore update-runtime \
     --runtime-id restaurant_booking_orchestrator-A5ITpVHRPw \
     --tracing-config Mode=Active
   ```

## Post-Deployment

- [ ] Monitor error rates for 24 hours
- [ ] Review cost metrics
- [ ] Test with real users (beta group)
- [ ] Document any issues

## Rollback Plan

If issues occur:
```bash
# Revert to previous runtime version
aws bedrock-agentcore update-runtime \
  --runtime-id restaurant_booking_orchestrator-A5ITpVHRPw \
  --image-uri <PREVIOUS_IMAGE_URI>
```

## Current Status: ⚠️ NOT PRODUCTION READY

**Estimated Time to Production Ready**: 2-3 days
- Day 1: Security hardening + monitoring
- Day 2: Testing + validation
- Day 3: Production deployment + monitoring
