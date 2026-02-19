# Quick Start: Automated Cognito Setup for Weather API

## 🚀 One-Command Setup

```bash
cd mock-weather-service
python3 update_cognito_for_weather.py us-east-1_v7ilQRXCR us-east-1
```

## 📋 What This Script Does

1. ✅ Checks if `custom:tier` attribute exists
2. ✅ Creates test users (normal_user, gold_user)
3. ✅ Sets tier attributes for each user
4. ✅ Sets permanent passwords
5. ✅ Verifies user attributes
6. ✅ Tests user login
7. ✅ Displays JWT tokens

## 👥 Created Users

| Username | Tier | Password | Email |
|----------|------|----------|-------|
| normal_user | normal | WeatherTest123! | normal@weather-api.example.com |
| gold_user | gold | WeatherTest123! | gold@weather-api.example.com |

## ⚠️ Important Note

**Custom attributes cannot be added to existing user pools via API.**

If the script reports that the `custom:tier` attribute is missing:

1. Open AWS Console → Cognito → User Pools
2. Select: `us-east-1_v7ilQRXCR`
3. Go to: Sign-up experience → Custom attributes
4. Add attribute:
   - Name: `tier`
   - Type: `String`
   - Min: 4, Max: 10
   - Mutable: Yes
5. Re-run the script

## 🧪 Test Login

After running the script, test user login:

```bash
# Get access token for normal user
aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_v7ilQRXCR \
  --client-id <CLIENT_ID> \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=normal_user,PASSWORD=WeatherTest123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text

# Get access token for gold user
aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_v7ilQRXCR \
  --client-id <CLIENT_ID> \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=gold_user,PASSWORD=WeatherTest123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text
```

## 🔍 Verify JWT Token

Decode the token to verify it contains `custom:tier`:

```bash
# Copy token from above command
echo "<ACCESS_TOKEN>" | cut -d'.' -f2 | base64 -d | jq
```

Expected claims:
```json
{
  "username": "normal_user",
  "custom:tier": "normal",
  "exp": 1234567890,
  "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_v7ilQRXCR"
}
```

## 📝 Next Steps

After successful setup:

1. ✅ Phase 1 Complete (Cognito configured)
2. ➡️ Proceed to Phase 2: Implement `auth.py`
3. ➡️ Proceed to Phase 3: Implement `middleware.py`
4. ➡️ Proceed to Phase 4: Update `app.py`

## 🔧 Troubleshooting

### Error: "Custom attribute 'tier' not found"
**Solution:** Add the attribute manually via AWS Console (see note above)

### Error: "User already exists"
**Solution:** Script will update existing users with tier attribute

### Error: "InvalidPasswordException"
**Solution:** Password must meet Cognito requirements (uppercase, lowercase, number, special char)

### Error: "ResourceNotFoundException"
**Solution:** Verify User Pool ID is correct: `us-east-1_v7ilQRXCR`

## 📊 Script Output Example

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
     Token: eyJraWQiOiJxxx...
   ✓ gold_user: Login successful
     Token: eyJraWQiOiJyyy...

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
