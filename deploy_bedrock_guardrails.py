"""
Deploy AWS Bedrock Guardrails for content filtering and topic blocking.
Provides LLM-level protection against harmful content and off-topic queries.
"""
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()


def create_guardrail():
    """Create Bedrock Guardrail with content filters and topic blocking"""
    
    bedrock = boto3.client("bedrock", region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    guardrail_config = {
        "name": "RestaurantBookingGuardrail",
        "description": "Content filtering and topic blocking for restaurant booking system",
        
        # Content filters (hate, insults, sexual, violence, misconduct)
        "contentPolicyConfig": {
            "filtersConfig": [
                {
                    "type": "HATE",
                    "inputStrength": "HIGH",
                    "outputStrength": "HIGH"
                },
                {
                    "type": "INSULTS",
                    "inputStrength": "HIGH",
                    "outputStrength": "HIGH"
                },
                {
                    "type": "SEXUAL",
                    "inputStrength": "HIGH",
                    "outputStrength": "HIGH"
                },
                {
                    "type": "VIOLENCE",
                    "inputStrength": "MEDIUM",
                    "outputStrength": "MEDIUM"
                },
                {
                    "type": "MISCONDUCT",
                    "inputStrength": "MEDIUM",
                    "outputStrength": "MEDIUM"
                }
            ]
        },
        
        # Topic blocking (deny off-topic queries)
        "topicPolicyConfig": {
            "topicsConfig": [
                {
                    "name": "PoliticalDiscussion",
                    "definition": "Political opinions, elections, government policies",
                    "examples": [
                        "What do you think about the president?",
                        "Tell me about political parties"
                    ],
                    "type": "DENY"
                },
                {
                    "name": "MedicalAdvice",
                    "definition": "Medical diagnosis, treatment recommendations, health advice",
                    "examples": [
                        "What medicine should I take?",
                        "Diagnose my symptoms"
                    ],
                    "type": "DENY"
                },
                {
                    "name": "FinancialAdvice",
                    "definition": "Investment advice, stock recommendations, financial planning",
                    "examples": [
                        "Should I invest in stocks?",
                        "Give me financial advice"
                    ],
                    "type": "DENY"
                },
                {
                    "name": "LegalAdvice",
                    "definition": "Legal opinions, contract interpretation, legal guidance",
                    "examples": [
                        "Can I sue someone?",
                        "What are my legal rights?"
                    ],
                    "type": "DENY"
                }
            ]
        },
        
        # Sensitive information filters (PII blocking)
        "sensitiveInformationPolicyConfig": {
            "piiEntitiesConfig": [
                {"type": "EMAIL", "action": "BLOCK"},
                {"type": "PHONE", "action": "BLOCK"},
                {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
                {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"},
                {"type": "US_BANK_ACCOUNT_NUMBER", "action": "BLOCK"}
            ]
        },
        
        # Word filters (profanity blocking)
        "wordPolicyConfig": {
            "wordsConfig": [
                {"text": "profanity1"},
                {"text": "profanity2"}
            ],
            "managedWordListsConfig": [
                {"type": "PROFANITY"}
            ]
        },
        
        # Blocked messaging
        "blockedInputMessaging": "I can only help with restaurant bookings and dining recommendations. Please ask about restaurants, reservations, or food.",
        "blockedOutputsMessaging": "I cannot provide that type of information. I can only assist with restaurant bookings."
    }
    
    try:
        response = bedrock.create_guardrail(**guardrail_config)
        
        guardrail_id = response["guardrailId"]
        guardrail_arn = response["guardrailArn"]
        
        print("=" * 80)
        print("✅ BEDROCK GUARDRAIL CREATED")
        print("=" * 80)
        print(f"Guardrail ID: {guardrail_id}")
        print(f"Guardrail ARN: {guardrail_arn}")
        
        # Store in SSM Parameter Store
        ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION", "us-east-1"))
        
        ssm.put_parameter(
            Name="/restaurant-booking/guardrail/id",
            Value=guardrail_id,
            Type="String",
            Overwrite=True
        )
        
        ssm.put_parameter(
            Name="/restaurant-booking/guardrail/arn",
            Value=guardrail_arn,
            Type="String",
            Overwrite=True
        )
        
        print("\n✅ Guardrail ID stored in SSM: /restaurant-booking/guardrail/id")
        
        # Create version
        version_response = bedrock.create_guardrail_version(
            guardrailIdentifier=guardrail_id,
            description="Initial version"
        )
        
        version = version_response["version"]
        print(f"✅ Guardrail Version: {version}")
        
        print("\n" + "=" * 80)
        print("GUARDRAIL CONFIGURATION")
        print("=" * 80)
        print("✅ Content Filters: HATE, INSULTS, SEXUAL, VIOLENCE, MISCONDUCT")
        print("✅ Topic Blocking: Politics, Medical, Financial, Legal advice")
        print("✅ PII Blocking: Email, Phone, Credit Card, SSN, Bank Account")
        print("✅ Profanity Filter: Enabled")
        
        return guardrail_id, guardrail_arn, version
        
    except bedrock.exceptions.ConflictException:
        print("⚠️  Guardrail already exists. Retrieving existing guardrail...")
        
        # List guardrails to find existing one
        response = bedrock.list_guardrails()
        for guardrail in response.get("guardrails", []):
            if guardrail["name"] == "RestaurantBookingGuardrail":
                guardrail_id = guardrail["id"]
                guardrail_arn = guardrail["arn"]
                
                print(f"✅ Found existing guardrail: {guardrail_id}")
                return guardrail_id, guardrail_arn, "1"
        
        raise Exception("Guardrail exists but could not be found")


def test_guardrail(guardrail_id: str, version: str):
    """Test guardrail with sample inputs"""
    
    bedrock_runtime = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    test_cases = [
        ("Find Italian restaurants in Boston", True),
        ("What do you think about politics?", False),
        ("Give me medical advice", False),
        ("My email is test@example.com", False),
        ("Book a table for 4 people", True)
    ]
    
    print("\n" + "=" * 80)
    print("TESTING GUARDRAIL")
    print("=" * 80)
    
    for user_input, should_pass in test_cases:
        try:
            response = bedrock_runtime.converse(
                modelId="amazon.nova-lite-v1:0",
                messages=[{"role": "user", "content": [{"text": user_input}]}],
                guardrailConfig={
                    "guardrailIdentifier": guardrail_id,
                    "guardrailVersion": version,
                    "trace": "enabled"
                }
            )
            
            status = "✅ PASSED" if should_pass else "❌ SHOULD BLOCK"
            print(f"\n{status}: '{user_input}'")
            
        except Exception as e:
            status = "✅ BLOCKED" if not should_pass else "❌ SHOULD PASS"
            print(f"\n{status}: '{user_input}'")
            print(f"   Reason: {str(e)[:100]}")


def update_env_file(guardrail_id: str):
    """Update .env file with guardrail ID"""
    
    env_path = "/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem/.env"
    
    # Read existing .env
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    # Add or update guardrail ID
    found = False
    for i, line in enumerate(lines):
        if line.startswith("GUARDRAIL_ID="):
            lines[i] = f"GUARDRAIL_ID={guardrail_id}\n"
            found = True
            break
    
    if not found:
        lines.append(f"\n# Bedrock Guardrail\nGUARDRAIL_ID={guardrail_id}\n")
    
    # Write back
    with open(env_path, "w") as f:
        f.writelines(lines)
    
    print(f"\n✅ Updated .env with GUARDRAIL_ID={guardrail_id}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DEPLOYING BEDROCK GUARDRAILS")
    print("=" * 80)
    
    guardrail_id, guardrail_arn, version = create_guardrail()
    
    # Test guardrail
    test_guardrail(guardrail_id, version)
    
    # Update .env
    update_env_file(guardrail_id)
    
    print("\n" + "=" * 80)
    print("✅ GUARDRAIL DEPLOYMENT COMPLETE")
    print("=" * 80)
    print(f"\nTo use in LLM calls:")
    print(f"""
response = bedrock.converse(
    modelId="amazon.nova-lite-v1:0",
    messages=[...],
    guardrailConfig={{
        "guardrailIdentifier": "{guardrail_id}",
        "guardrailVersion": "{version}"
    }}
)
""")
