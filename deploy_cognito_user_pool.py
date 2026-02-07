#!/usr/bin/env python3
"""Deploy Cognito User Pool for Restaurant Booking Gateway Authentication."""
import boto3
import sys
from boto3.session import Session

def put_ssm_parameter(name: str, value: str):
    """Store parameter in SSM."""
    ssm = boto3.client("ssm")
    ssm.put_parameter(Name=name, Value=value, Type="String", Overwrite=True)
    print(f"✅ Stored in SSM: {name}")

def get_or_create_user_pool(cognito, pool_name, region):
    """Get existing or create new user pool."""
    response = cognito.list_user_pools(MaxResults=60)
    for pool in response["UserPools"]:
        if pool["Name"] == pool_name:
            print(f"✅ Found existing user pool: {pool['Id']}")
            return pool["Id"]
    
    print(f"🆕 Creating new user pool: {pool_name}")
    created = cognito.create_user_pool(PoolName=pool_name)
    user_pool_id = created["UserPool"]["Id"]
    
    # Create domain
    domain = user_pool_id.replace("_", "").lower()
    cognito.create_user_pool_domain(Domain=domain, UserPoolId=user_pool_id)
    print(f"✅ Created domain: {domain}")
    
    return user_pool_id

def get_or_create_resource_server(cognito, user_pool_id, server_id, server_name, scopes):
    """Get existing or create new resource server."""
    try:
        cognito.describe_resource_server(UserPoolId=user_pool_id, Identifier=server_id)
        print(f"✅ Found existing resource server: {server_id}")
        return server_id
    except cognito.exceptions.ResourceNotFoundException:
        print(f"🆕 Creating resource server: {server_id}")
        cognito.create_resource_server(
            UserPoolId=user_pool_id,
            Identifier=server_id,
            Name=server_name,
            Scopes=scopes
        )
        return server_id

def get_or_create_m2m_client(cognito, user_pool_id, client_name, server_id):
    """Get existing or create new M2M client."""
    response = cognito.list_user_pool_clients(UserPoolId=user_pool_id, MaxResults=60)
    for client in response["UserPoolClients"]:
        if client["ClientName"] == client_name:
            describe = cognito.describe_user_pool_client(
                UserPoolId=user_pool_id, 
                ClientId=client["ClientId"]
            )
            print(f"✅ Found existing M2M client: {client['ClientId']}")
            return client["ClientId"], describe["UserPoolClient"]["ClientSecret"]
    
    print(f"🆕 Creating M2M client: {client_name}")
    created = cognito.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=client_name,
        GenerateSecret=True,
        AllowedOAuthFlows=["client_credentials"],
        AllowedOAuthScopes=[
            f"{server_id}/invoke"
        ],
        AllowedOAuthFlowsUserPoolClient=True,
        SupportedIdentityProviders=["COGNITO"],
        ExplicitAuthFlows=["ALLOW_REFRESH_TOKEN_AUTH"]
    )
    return created["UserPoolClient"]["ClientId"], created["UserPoolClient"]["ClientSecret"]

def setup_cognito(region_name: str = "us-east-1"):
    """Setup Cognito User Pool for Gateway authentication."""
    print(f"🚀 Setting up Cognito User Pool in {region_name}...")
    
    cognito = boto3.client("cognito-idp", region_name=region_name)
    
    # Configuration
    USER_POOL_NAME = "restaurant-booking-gateway-pool"
    RESOURCE_SERVER_ID = "restaurant-booking-auth"
    RESOURCE_SERVER_NAME = "RestaurantBookingAuth"
    CLIENT_NAME = "restaurant-booking-client"
    SCOPES = [
        {"ScopeName": "invoke", "ScopeDescription": "Invoke gateway tools"}
    ]
    
    # Create/get user pool
    user_pool_id = get_or_create_user_pool(cognito, USER_POOL_NAME, region_name)
    put_ssm_parameter("/app/restaurant-booking/user_pool_id", user_pool_id)
    
    # Create/get resource server
    get_or_create_resource_server(
        cognito, user_pool_id, RESOURCE_SERVER_ID, RESOURCE_SERVER_NAME, SCOPES
    )
    
    # Create/get M2M client
    client_id, client_secret = get_or_create_m2m_client(
        cognito, user_pool_id, CLIENT_NAME, RESOURCE_SERVER_ID
    )
    put_ssm_parameter("/app/restaurant-booking/client_id", client_id)
    put_ssm_parameter("/app/restaurant-booking/client_secret", client_secret)
    
    # Create scope string
    scope_string = f"{RESOURCE_SERVER_ID}/invoke"
    put_ssm_parameter("/app/restaurant-booking/scope", scope_string)
    
    # Discovery URL
    discovery_url = f"https://cognito-idp.{region_name}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
    
    print(f"\n✅ Cognito setup complete!")
    print(f"\n📋 Configuration:")
    print(f"   User Pool ID: {user_pool_id}")
    print(f"   Client ID: {client_id}")
    print(f"   Discovery URL: {discovery_url}")
    print(f"   Scope: {scope_string}")
    
    return {
        "user_pool_id": user_pool_id,
        "client_id": client_id,
        "client_secret": client_secret,
        "discovery_url": discovery_url,
        "scope": scope_string
    }

if __name__ == "__main__":
    region = sys.argv[1] if len(sys.argv) > 1 else "us-east-1"
    
    try:
        config = setup_cognito(region)
        
        print(f"\n🎉 Setup complete!")
        print(f"\n📋 Next steps:")
        print(f"   1. Run: python3 deploy_agentcore_gateway.py")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
