"""
Update existing Bedrock Guardrail with proper policies.
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

bedrock = boto3.client("bedrock", region_name=os.getenv("AWS_REGION", "us-east-1"))
guardrail_id = os.getenv("GUARDRAIL_ID")

print(f"Updating guardrail: {guardrail_id}")

response = bedrock.update_guardrail(
    guardrailIdentifier=guardrail_id,
    name="RestaurantBookingGuardrail",
    description="Content filtering and topic blocking for restaurant booking system",
    
    # Content filters
    contentPolicyConfig={
        "filtersConfig": [
            {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "INSULTS", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "SEXUAL", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "VIOLENCE", "inputStrength": "MEDIUM", "outputStrength": "MEDIUM"},
            {"type": "MISCONDUCT", "inputStrength": "MEDIUM", "outputStrength": "MEDIUM"}
        ]
    },
    
    # Topic blocking
    topicPolicyConfig={
        "topicsConfig": [
            {
                "name": "PoliticalDiscussion",
                "definition": "Political opinions, elections, government policies",
                "examples": ["What do you think about the president?", "Tell me about political parties"],
                "type": "DENY"
            },
            {
                "name": "MedicalAdvice",
                "definition": "Medical diagnosis, treatment recommendations, health advice",
                "examples": ["What medicine should I take?", "Diagnose my symptoms"],
                "type": "DENY"
            },
            {
                "name": "FinancialAdvice",
                "definition": "Investment advice, stock recommendations, financial planning",
                "examples": ["Should I invest in stocks?", "Give me financial advice"],
                "type": "DENY"
            }
        ]
    },
    
    # PII blocking
    sensitiveInformationPolicyConfig={
        "piiEntitiesConfig": [
            {"type": "EMAIL", "action": "BLOCK"},
            {"type": "PHONE", "action": "BLOCK"},
            {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
            {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"}
        ]
    },
    
    # Profanity
    wordPolicyConfig={
        "managedWordListsConfig": [{"type": "PROFANITY"}]
    },
    
    blockedInputMessaging="I can only help with restaurant bookings. Please ask about restaurants or reservations.",
    blockedOutputsMessaging="I cannot provide that information. I can only assist with restaurant bookings."
)

print(f"✅ Guardrail updated: {response['guardrailId']}")

# Create new version
version_response = bedrock.create_guardrail_version(
    guardrailIdentifier=guardrail_id,
    description="Updated with content filters and topic blocking"
)

print(f"✅ New version created: {version_response['version']}")
