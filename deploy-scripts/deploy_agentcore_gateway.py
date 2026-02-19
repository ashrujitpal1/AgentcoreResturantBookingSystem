#!/usr/bin/env python3
"""Deploy AgentCore Gateway with Lambda MCP Tools."""
import boto3
import sys
import time

# Lambda ARNs from SAM deployment
LAMBDA_ARNS = {
    'fetchRestaurantDetails': 'arn:aws:lambda:us-east-1:696072349808:function:fetchRestaurantDetails-dev',
    'fetchRestaurantDetailsById': 'arn:aws:lambda:us-east-1:696072349808:function:fetchRestaurantDetailsById-dev',
    'searchUserDetails': 'arn:aws:lambda:us-east-1:696072349808:function:searchUserDetails-dev',
    'registerUser': 'arn:aws:lambda:us-east-1:696072349808:function:registerUser-dev',
    'tokenAmountCalculation': 'arn:aws:lambda:us-east-1:696072349808:function:tokenAmountCalculation-dev',
    'bookATable': 'arn:aws:lambda:us-east-1:696072349808:function:bookATable-dev',
    'paymentAPI': 'arn:aws:lambda:us-east-1:696072349808:function:paymentAPI-dev',
    'getCurrentDateTime': 'arn:aws:lambda:us-east-1:696072349808:function:getCurrentDateTime-dev'
}

def get_ssm_parameter(name: str) -> str:
    """Get parameter from SSM."""
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=name)
    return response["Parameter"]["Value"]

def put_ssm_parameter(name: str, value: str):
    """Store parameter in SSM."""
    ssm = boto3.client("ssm")
    ssm.put_parameter(Name=name, Value=value, Type="String", Overwrite=True)
    print(f"✅ Stored in SSM: {name}")

def create_gateway_role(region: str, account_id: str):
    """Create IAM role for Gateway."""
    iam = boto3.client('iam')
    role_name = 'agentcore-restaurant-gateway-role'
    
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {"aws:SourceAccount": account_id},
                "ArnLike": {"aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"}
            }
        }]
    }
    
    role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:*",
                "bedrock:*",
                "lambda:InvokeFunction"
            ],
            "Resource": "*"
        }]
    }
    
    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=str(assume_role_policy).replace("'", '"')
        )
        role_arn = response['Role']['Arn']
        print(f"✅ Created IAM role: {role_name}")
        
        time.sleep(10)  # Wait for role propagation
        
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="GatewayPolicy",
            PolicyDocument=str(role_policy).replace("'", '"')
        )
        print(f"✅ Attached policy to role")
        
        time.sleep(10)
        return role_arn
        
    except iam.exceptions.EntityAlreadyExistsException:
        response = iam.get_role(RoleName=role_name)
        print(f"✅ Using existing role: {role_name}")
        return response['Role']['Arn']

def create_gateway(region: str):
    """Create AgentCore Gateway with Cognito auth."""
    print(f"🚀 Creating AgentCore Gateway...")
    
    gateway_client = boto3.client('bedrock-agentcore-control', region_name=region)
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    # Get Cognito config
    user_pool_id = get_ssm_parameter("/app/restaurant-booking/user_pool_id")
    client_id = get_ssm_parameter("/app/restaurant-booking/client_id")
    discovery_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
    
    # Create role
    role_arn = create_gateway_role(region, account_id)
    
    # Auth config
    auth_config = {
        "customJWTAuthorizer": {
            "allowedClients": [client_id],
            "discoveryUrl": discovery_url
        }
    }
    
    gateway_name = 'restaurant-booking-gateway'
    
    try:
        response = gateway_client.create_gateway(
            name=gateway_name,
            roleArn=role_arn,
            protocolType='MCP',
            authorizerType='CUSTOM_JWT',
            authorizerConfiguration=auth_config,
            description='Restaurant Booking Gateway with Lambda MCP tools'
        )
        
        gateway_id = response["gatewayId"]
        gateway_url = response["gatewayUrl"]
        
        print(f"✅ Gateway created: {gateway_id}")
        print(f"   URL: {gateway_url}")
        
        put_ssm_parameter("/app/restaurant-booking/gateway_id", gateway_id)
        put_ssm_parameter("/app/restaurant-booking/gateway_url", gateway_url)
        
        return gateway_id, gateway_url
        
    except gateway_client.exceptions.ConflictException:
        print(f"✅ Gateway '{gateway_name}' already exists")
        gateway_id = get_ssm_parameter("/app/restaurant-booking/gateway_id")
        gateway_url = get_ssm_parameter("/app/restaurant-booking/gateway_url")
        return gateway_id, gateway_url

def register_lambda_tools(gateway_id: str, region: str):
    """Register all 7 Lambda functions as MCP tools."""
    print(f"\n🔧 Registering Lambda tools...")
    
    gateway_client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    tools = [
        {
            'name': 'fetchRestaurantDetails',
            'lambda_arn': LAMBDA_ARNS['fetchRestaurantDetails'],
            'description': 'Search restaurants by city, cuisine, price range, and rating with pagination',
            'schema': {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "cuisine": {"type": "string", "description": "Cuisine type"},
                    "priceRange": {"type": "string", "description": "Price range ($, $$, $$$, $$$$)"},
                    "minRating": {"type": "number", "description": "Minimum rating (0-5)"},
                    "requestId": {"type": "string", "description": "Optional request ID for caching and observability"},
                    "maxResults": {"type": "integer", "description": "Max results per page (default: 50, max: 100)"},
                    "nextToken": {"type": "string", "description": "Pagination token from previous response"}
                }
            }
        },
        {
            'name': 'fetchRestaurantDetailsById',
            'lambda_arn': LAMBDA_ARNS['fetchRestaurantDetailsById'],
            'description': 'Get specific restaurant details by ID',
            'schema': {
                "type": "object",
                "properties": {
                    "restaurantId": {"type": "string", "description": "Restaurant ID"},
                    "requestId": {"type": "string", "description": "Optional request ID for caching and observability"}
                },
                "required": ["restaurantId"]
            }
        },
        {
            'name': 'searchUserDetails',
            'lambda_arn': LAMBDA_ARNS['searchUserDetails'],
            'description': 'Find user by username or mobile number',
            'schema': {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Username"},
                    "userMobileNo": {"type": "string", "description": "Mobile number"},
                    "requestId": {"type": "string", "description": "Optional request ID for caching and observability"}
                }
            }
        },
        {
            'name': 'registerUser',
            'lambda_arn': LAMBDA_ARNS['registerUser'],
            'description': 'Register new user',
            'schema': {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Username"},
                    "mobileNo": {"type": "string", "description": "Mobile number"},
                    "userCity": {"type": "string", "description": "User city"},
                    "requestId": {"type": "string", "description": "Idempotency key"}
                },
                "required": ["username", "mobileNo", "userCity", "requestId"]
            }
        },
        {
            'name': 'tokenAmountCalculation',
            'lambda_arn': LAMBDA_ARNS['tokenAmountCalculation'],
            'description': 'Calculate booking token amount',
            'schema': {
                "type": "object",
                "properties": {
                    "noOfGuests": {"type": "integer", "description": "Number of guests"},
                    "mealType": {"type": "string", "description": "Meal type (breakfast/lunch/dinner)"},
                    "restaurantTier": {"type": "string", "description": "Restaurant tier ($-$$$$)"},
                    "requestId": {"type": "string", "description": "Optional request ID for caching and observability"}
                },
                "required": ["noOfGuests"]
            }
        },
        {
            'name': 'bookATable',
            'lambda_arn': LAMBDA_ARNS['bookATable'],
            'description': 'Create restaurant booking',
            'schema': {
                "type": "object",
                "properties": {
                    "restaurantId": {"type": "string"},
                    "userName": {"type": "string"},
                    "userMobileNo": {"type": "string"},
                    "date": {"type": "string", "description": "Booking date (YYYY-MM-DD)"},
                    "time": {"type": "string", "description": "Booking time (HH:MM)"},
                    "type": {"type": "string", "description": "Meal type"},
                    "cityName": {"type": "string"},
                    "noOfGuests": {"type": "integer"},
                    "tokenAmount": {"type": "number"},
                    "requestId": {"type": "string"}
                },
                "required": ["restaurantId", "userName", "userMobileNo", "date", "time", "noOfGuests", "requestId"]
            }
        },
        {
            'name': 'paymentAPI',
            'lambda_arn': LAMBDA_ARNS['paymentAPI'],
            'description': 'Process payment for booking',
            'schema': {
                "type": "object",
                "properties": {
                    "userId": {"type": "string"},
                    "restaurantId": {"type": "string"},
                    "bookingId": {"type": "string"},
                    "tokenAmount": {"type": "number"},
                    "paymentMethod": {"type": "string"},
                    "requestId": {"type": "string"}
                },
                "required": ["userId", "restaurantId", "tokenAmount", "requestId"]
            }
        },
        {
            'name': 'getCurrentDateTime',
            'lambda_arn': LAMBDA_ARNS['getCurrentDateTime'],
            'description': 'Get current date and time in specified timezone',
            'schema': {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Timezone (default: UTC)"}
                }
            }
        }
    ]
    
    for tool in tools:
        target_name = f"{tool['name']}-target-{int(time.time())}"
        
        target_config = {
            "mcp": {
                "lambda": {
                    "lambdaArn": tool['lambda_arn'],
                    "toolSchema": {
                        "inlinePayload": [{
                            "name": tool['name'],
                            "description": tool['description'],
                            "inputSchema": tool['schema']
                        }]
                    }
                }
            }
        }
        
        credential_config = [{"credentialProviderType": "GATEWAY_IAM_ROLE"}]
        
        try:
            response = gateway_client.create_gateway_target(
                gatewayIdentifier=gateway_id,
                name=target_name,
                description=f"Lambda target for {tool['name']}",
                targetConfiguration=target_config,
                credentialProviderConfigurations=credential_config
            )
            print(f"✅ Registered: {tool['name']}")
            
        except gateway_client.exceptions.ConflictException:
            print(f"⚠️  Tool '{tool['name']}' already registered")

if __name__ == "__main__":
    region = sys.argv[1] if len(sys.argv) > 1 else "us-east-1"
    
    try:
        gateway_id, gateway_url = create_gateway(region)
        register_lambda_tools(gateway_id, region)
        
        print(f"\n🎉 Gateway setup complete!")
        print(f"\n📋 Configuration:")
        print(f"   Gateway ID: {gateway_id}")
        print(f"   Gateway URL: {gateway_url}")
        print(f"   Tools registered: 7")
        print(f"\n📋 Next steps:")
        print(f"   1. Update .env with GATEWAY_ID and GATEWAY_URL")
        print(f"   2. Run: python3 deploy_agentcore_memory.py")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
