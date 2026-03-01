# Pre-Deployment Checklist

Complete this checklist before running deployment.

## ☑️ AWS Account Setup

- [ ] AWS CLI installed and configured
  ```bash
  aws --version
  aws configure
  ```

- [ ] AWS credentials verified
  ```bash
  aws sts get-caller-identity
  ```

- [ ] Correct AWS region set (us-east-1 recommended)
  ```bash
  export AWS_REGION=us-east-1
  ```

## ☑️ Bedrock Model Access

- [ ] Navigate to AWS Console → Bedrock → Model access
- [ ] Request access to these models:
  - [ ] `anthropic.claude-3-5-sonnet-20241022-v2:0`
  - [ ] `amazon.nova-lite-v1:0`
  - [ ] `amazon.nova-micro-v1:0`
- [ ] Wait for "Access granted" status (~2-5 minutes)

## ☑️ IAM Permissions

Your IAM user/role needs these permissions:
- [ ] `bedrock:*` (Bedrock full access)
- [ ] `lambda:*` (Lambda management)
- [ ] `dynamodb:*` (DynamoDB management)
- [ ] `s3:*` (S3 bucket operations)
- [ ] `cognito-idp:*` (Cognito User Pool)
- [ ] `iam:CreateRole`, `iam:AttachRolePolicy` (IAM role creation)
- [ ] `ssm:PutParameter`, `ssm:GetParameter` (Parameter Store)
- [ ] `logs:*` (CloudWatch Logs)

**Quick check:**
```bash
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[0]'
```

## ☑️ Development Tools

- [ ] Python 3.11+ installed
  ```bash
  python3 --version
  ```

- [ ] pip installed
  ```bash
  pip --version
  ```

- [ ] AWS SAM CLI installed
  ```bash
  sam --version
  # If not: pip install aws-sam-cli
  ```

- [ ] Docker installed (for SAM local testing - optional)
  ```bash
  docker --version
  ```

## ☑️ Project Setup

- [ ] Repository cloned
  ```bash
  cd AgentcoreResturantBookingSystem
  ```

- [ ] Python dependencies installed
  ```bash
  pip install -r requirements.txt
  ```

- [ ] Bedrock AgentCore toolkit installed
  ```bash
  pip install bedrock-agentcore-starter-toolkit
  ```

## ☑️ Cost Awareness

Estimated monthly costs for development:
- [ ] Bedrock model usage: $10-30
- [ ] Lambda invocations: $1-5
- [ ] DynamoDB: $1-3
- [ ] AgentCore Runtime: $5-15
- [ ] S3 storage: <$1
- **Total: ~$20-50/month**

Set up billing alerts:
```bash
aws budgets create-budget --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget.json
```

## ☑️ Network Configuration (Optional)

If deploying with VPC:
- [ ] VPC created with private subnets
- [ ] NAT Gateway configured
- [ ] Security groups defined
- [ ] VPC endpoints for Bedrock (optional)

## ☑️ Pre-Deployment Verification

Run these commands to verify setup:

```bash
# 1. Check AWS access
aws sts get-caller-identity

# 2. Check Bedrock access
aws bedrock list-foundation-models --region us-east-1 | grep claude

# 3. Check Python dependencies
python3 -c "import boto3, botocore; print('✅ boto3 installed')"

# 4. Check SAM CLI
sam --version

# 5. Verify project structure
ls -la src/ prompts/ deploy-scripts/
```

## ☑️ Ready to Deploy

Once all items are checked:

**Option 1: Quick Start (Automated)**
```bash
./quickstart.sh
```

**Option 2: Step-by-Step**
```bash
cd deploy-scripts
./deploy.sh
```

**Option 3: Manual (Individual Steps)**
```bash
# See CLEAN_SLATE_DEPLOYMENT.md for detailed steps
```

## 🚨 Common Issues

### Issue: "Model access denied"
**Solution:** Request model access in Bedrock console (takes 2-5 minutes)

### Issue: "Insufficient permissions"
**Solution:** Attach `PowerUserAccess` or create custom policy with required permissions

### Issue: "SAM CLI not found"
**Solution:** `pip install aws-sam-cli`

### Issue: "Region not supported"
**Solution:** Use `us-east-1` (most Bedrock features available)

## 📞 Support

- AWS Bedrock Documentation: https://docs.aws.amazon.com/bedrock/
- AgentCore Documentation: https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html
- Project Documentation: `docs/architecture-overview.md`

---

**Next:** Run `./quickstart.sh` to begin deployment
