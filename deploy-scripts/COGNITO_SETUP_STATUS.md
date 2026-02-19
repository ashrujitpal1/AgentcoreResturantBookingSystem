# Cognito Setup Status - Weather API Authentication

## 🔍 Current Status

**Script Executed:** ✅ `update_cognito_for_weather.py`  
**Result:** ⚠️ Manual action required

## ⚠️ Why Manual Action is Needed

AWS Cognito **does not allow** adding custom attributes to existing user pools via API. This is an AWS platform limitation, not a script issue.

**The custom attribute `custom:tier` must be added manually via AWS Console.**

## 🛠️ Two Options to Complete Setup

### Option 1: Interactive Script (Recommended)

Run the interactive setup script that guides you through the process:

```bash
cd /Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem
./deploy-scripts/setup_cognito_weather.sh
```

This script will:
1. Check if the attribute exists
2. Provide step-by-step instructions to add it
3. Wait for you to complete the manual step
4. Automatically create test users once attribute is added
5. Verify everything works

### Option 2: Manual Steps

#### Step 1: Add Custom Attribute (One-time, Manual)

1. Open AWS Console: https://console.aws.amazon.com/cognito/v2/idp/user-pools
2. Select User Pool: `us-east-1_v7ilQRXCR`
3. Navigate to: **Sign-up experience** → **Custom attributes**
4. Click: **Add custom attribute**
5. Configure:
   - **Attribute name:** `tier`
   - **Attribute data type:** `String`
   - **Minimum length:** `4`
   - **Maximum length:** `10`
   - **Mutable:** ✓ (checked)
6. Click: **Save changes**

#### Step 2: Run Script Again (Automated)

```bash
cd /Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem
python3 deploy-scripts/update_cognito_for_weather.py us-east-1_v7ilQRXCR us-east-1
```

This will:
- ✅ Verify the attribute exists
- ✅ Create `normal_user` (tier: normal)
- ✅ Create `gold_user` (tier: gold)
- ✅ Set passwords: `WeatherTest123!`
- ✅ Test user login
- ✅ Display JWT tokens

## 📊 What Will Be Created

Once the custom attribute is added, the script will automatically create:

| Username | Tier | Password | Email | Access |
|----------|------|----------|-------|--------|
| normal_user | normal | WeatherTest123! | normal@weather-api.example.com | `/weather` only |
| gold_user | gold | WeatherTest123! | gold@weather-api.example.com | `/weather` + `/forecast` |

## 🔑 Expected Output After Completion

```
🚀 Updating Cognito User Pool for Weather API...
   User Pool ID: us-east-1_v7ilQRXCR
   Region: us-east-1

📋 Step 1: Custom Tier Attribute
------------------------------------------------------------
✅ Custom attribute 'tier' already exists

📋 Step 2: Create Test Users
------------------------------------------------------------
🆕 Creating user: normal_user
✅ Created user: normal_user (tier: normal)
🆕 Creating user: gold_user
✅ Created user: gold_user (tier: gold)

📋 Step 3: Verify User Attributes
------------------------------------------------------------
   ✓ normal_user: tier = normal
   ✓ gold_user: tier = gold

📋 Step 4: Test User Login
------------------------------------------------------------
Using Client ID: ta1t5evlj32p10t82gs33jcu8

   ✓ normal_user: Login successful
     Token: eyJraWQiOiJ...
   ✓ gold_user: Login successful
     Token: eyJraWQiOiJ...

============================================================
✅ Cognito Update Complete!
============================================================

📊 Summary:
   Users Created: 2/2
   User Pool ID: us-east-1_v7ilQRXCR

👥 Test Users:
   • normal_user (tier: normal)
     Password: WeatherTest123!
   • gold_user (tier: gold)
     Password: WeatherTest123!

🔑 JWKS URL:
   https://cognito-idp.us-east-1.amazonaws.com/us-east-1_v7ilQRXCR/.well-known/jwks.json

📝 Next Steps:
   1. Implement auth.py and middleware.py
   2. Update app.py with @require_auth decorators
   3. Test authentication with created users

🎉 Setup complete!
```

## 📝 Next Steps After Cognito Setup

Once Cognito is configured:

1. ✅ **Phase 1 Complete** - Cognito User Pool configured
2. ➡️ **Phase 2** - Implement `auth.py` (JWT verification)
3. ➡️ **Phase 3** - Implement `middleware.py` (authorization decorator)
4. ➡️ **Phase 4** - Update `app.py` with `@require_auth` decorators
5. ➡️ **Phase 5** - Test authentication with created users

## 🔧 Quick Commands

```bash
# Check if attribute exists
aws cognito-idp describe-user-pool \
  --user-pool-id us-east-1_v7ilQRXCR \
  --query 'UserPool.SchemaAttributes[?Name==`custom:tier`]'

# List users
aws cognito-idp list-users \
  --user-pool-id us-east-1_v7ilQRXCR

# Test login
aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_v7ilQRXCR \
  --client-id ta1t5evlj32p10t82gs33jcu8 \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=normal_user,PASSWORD=WeatherTest123!
```

## ❓ FAQ

**Q: Why can't the script add the attribute automatically?**  
A: AWS Cognito API does not support adding custom attributes to existing user pools. This is a platform limitation.

**Q: Will I lose existing users?**  
A: No, adding a custom attribute does not affect existing users.

**Q: Can I change the tier later?**  
A: Yes, the attribute is mutable. You can update user tiers anytime.

**Q: What if I already have users?**  
A: The script will update existing users with the tier attribute if they already exist.

---

**Ready to proceed?** Run the interactive setup script:

```bash
./deploy-scripts/setup_cognito_weather.sh
```
