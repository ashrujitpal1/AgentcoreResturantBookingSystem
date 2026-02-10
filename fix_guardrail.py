"""
Fix guardrail - remove topic blocking, keep only content/PII filters.
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

bedrock = boto3.client("bedrock", region_name=os.getenv("AWS_REGION", "us-east-1"))
guardrail_id = os.getenv("GUARDRAIL_ID")

print(f"Fixing guardrail: {guardrail_id}")

response = bedrock.update_guardrail(
    guardrailIdentifier=guardrail_id,
    name="RestaurantBookingGuardrail",
    description="Content filtering for restaurant booking system",
    
    # Content filters ONLY
    contentPolicyConfig={
        "filtersConfig": [
            {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "INSULTS", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "SEXUAL", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "VIOLENCE", "inputStrength": "MEDIUM", "outputStrength": "MEDIUM"},
            {"type": "MISCONDUCT", "inputStrength": "MEDIUM", "outputStrength": "MEDIUM"}
        ]
    },
    
    # NO TOPIC BLOCKING - handled by intent classifier
    
    # PII blocking
    sensitiveInformationPolicyConfig={
        "piiEntitiesConfig": [
            {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
            {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"}
        ]
    },
    
    # Profanity
    wordPolicyConfig={
        "managedWordListsConfig": [{"type": "PROFANITY"}]
    },
    
    blockedInputMessaging="I cannot process that request.",
    blockedOutputsMessaging="I cannot provide that information."
)

print(f"✅ Guardrail updated: {response['guardrailId']}")

# Create new version
version_response = bedrock.create_guardrail_version(
    guardrailIdentifier=guardrail_id,
    description="Fixed - removed topic blocking"
)

print(f"✅ New version created: {version_response['version']}")
print("\nUpdate agents to use version 3")
