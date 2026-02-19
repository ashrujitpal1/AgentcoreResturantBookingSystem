#!/usr/bin/env python3
"""Update Cognito User Pool with custom tier attribute and create test users."""
import boto3
import sys

def add_custom_tier_attribute(cognito, user_pool_id):
    """Add custom:tier attribute to existing user pool."""
    try:
        # Check if attribute already exists
        pool = cognito.describe_user_pool(UserPoolId=user_pool_id)
        for attr in pool['UserPool'].get('SchemaAttributes', []):
            if attr.get('Name') == 'custom:tier':
                print(f"✅ Custom attribute 'tier' already exists")
                return True
        
        # Note: Custom attributes cannot be added to existing user pools via API
        # They must be added during pool creation or via AWS Console
        print(f"⚠️  Custom attribute 'tier' not found")
        print(f"   Please add manually via AWS Console:")
        print(f"   1. Go to Cognito → User Pool: {user_pool_id}")
        print(f"   2. Sign-up experience → Custom attributes → Add")
        print(f"   3. Name: tier, Type: String, Min: 4, Max: 10, Mutable: Yes")
        return False
        
    except Exception as e:
        print(f"❌ Error checking custom attribute: {e}")
        return False

def create_test_user(cognito, user_pool_id, username, email, tier, password):
    """Create test user with tier attribute."""
    try:
        # Check if user exists
        try:
            cognito.admin_get_user(UserPoolId=user_pool_id, Username=username)
            print(f"✅ User '{username}' already exists")
            
            # Update tier attribute
            cognito.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=username,
                UserAttributes=[
                    {'Name': 'custom:tier', 'Value': tier}
                ]
            )
            print(f"   Updated tier to: {tier}")
            return True
            
        except cognito.exceptions.UserNotFoundException:
            # Create new user
            print(f"🆕 Creating user: {username}")
            cognito.admin_create_user(
                UserPoolId=user_pool_id,
                Username=username,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'custom:tier', 'Value': tier}
                ],
                TemporaryPassword="TempPass123!",
                MessageAction='SUPPRESS'
            )
            
            # Set permanent password
            cognito.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=username,
                Password=password,
                Permanent=True
            )
            print(f"✅ Created user: {username} (tier: {tier})")
            return True
            
    except Exception as e:
        print(f"❌ Error creating user '{username}': {e}")
        return False

def verify_user_tier(cognito, user_pool_id, username):
    """Verify user has tier attribute."""
    try:
        response = cognito.admin_get_user(UserPoolId=user_pool_id, Username=username)
        for attr in response.get('UserAttributes', []):
            if attr['Name'] == 'custom:tier':
                print(f"   ✓ {username}: tier = {attr['Value']}")
                return True
        print(f"   ✗ {username}: tier attribute missing")
        return False
    except Exception as e:
        print(f"   ✗ {username}: {e}")
        return False

def test_user_login(cognito, user_pool_id, client_id, username, password):
    """Test user login and verify JWT token."""
    try:
        response = cognito.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        access_token = response['AuthenticationResult']['AccessToken']
        print(f"   ✓ {username}: Login successful")
        print(f"     Token: {access_token[:50]}...")
        return True
        
    except Exception as e:
        print(f"   ✗ {username}: Login failed - {e}")
        return False

def update_cognito_for_weather_api(user_pool_id: str, region_name: str = "us-east-1"):
    """Update Cognito User Pool for Weather API authentication."""
    print(f"🚀 Updating Cognito User Pool for Weather API...")
    print(f"   User Pool ID: {user_pool_id}")
    print(f"   Region: {region_name}\n")
    
    cognito = boto3.client("cognito-idp", region_name=region_name)
    
    # Step 1: Check/Add custom tier attribute
    print("📋 Step 1: Custom Tier Attribute")
    print("-" * 60)
    has_tier = add_custom_tier_attribute(cognito, user_pool_id)
    
    if not has_tier:
        print("\n⚠️  Please add custom attribute manually and re-run this script")
        return False
    
    # Step 2: Create test users
    print("\n📋 Step 2: Create Test Users")
    print("-" * 60)
    
    users = [
        {
            "username": "normal_user",
            "email": "normal@weather-api.example.com",
            "tier": "normal",
            "password": "WeatherTest123!"
        },
        {
            "username": "gold_user",
            "email": "gold@weather-api.example.com",
            "tier": "gold",
            "password": "WeatherTest123!"
        }
    ]
    
    success_count = 0
    for user in users:
        if create_test_user(
            cognito, user_pool_id, 
            user["username"], user["email"], 
            user["tier"], user["password"]
        ):
            success_count += 1
    
    # Step 3: Verify users
    print(f"\n📋 Step 3: Verify User Attributes")
    print("-" * 60)
    for user in users:
        verify_user_tier(cognito, user_pool_id, user["username"])
    
    # Step 4: Get client ID for testing
    print(f"\n📋 Step 4: Test User Login")
    print("-" * 60)
    
    try:
        # Get first client ID
        clients = cognito.list_user_pool_clients(UserPoolId=user_pool_id, MaxResults=1)
        if clients['UserPoolClients']:
            client_id = clients['UserPoolClients'][0]['ClientId']
            print(f"Using Client ID: {client_id}\n")
            
            for user in users:
                test_user_login(
                    cognito, user_pool_id, client_id,
                    user["username"], user["password"]
                )
        else:
            print("⚠️  No client found for testing login")
    except Exception as e:
        print(f"⚠️  Could not test login: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ Cognito Update Complete!")
    print(f"{'='*60}")
    print(f"\n📊 Summary:")
    print(f"   Users Created: {success_count}/{len(users)}")
    print(f"   User Pool ID: {user_pool_id}")
    print(f"\n👥 Test Users:")
    for user in users:
        print(f"   • {user['username']} (tier: {user['tier']})")
        print(f"     Password: {user['password']}")
    
    print(f"\n🔑 JWKS URL:")
    print(f"   https://cognito-idp.{region_name}.amazonaws.com/{user_pool_id}/.well-known/jwks.json")
    
    print(f"\n📝 Next Steps:")
    print(f"   1. Implement auth.py and middleware.py")
    print(f"   2. Update app.py with @require_auth decorators")
    print(f"   3. Test authentication with created users")
    
    return True

if __name__ == "__main__":
    # Get user pool ID from command line or use default
    if len(sys.argv) > 1:
        user_pool_id = sys.argv[1]
    else:
        user_pool_id = "us-east-1_v7ilQRXCR"  # Default from .env
    
    region = sys.argv[2] if len(sys.argv) > 2 else "us-east-1"
    
    try:
        success = update_cognito_for_weather_api(user_pool_id, region)
        
        if success:
            print(f"\n🎉 Setup complete!")
        else:
            print(f"\n⚠️  Setup incomplete - manual steps required")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
