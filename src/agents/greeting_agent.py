"""
Greeting Agent - Fetches user preferences from long-term memory and displays personalized greeting.
"""
from typing import Dict, Any
import boto3
import os


class GreetingAgent:
    """Fetches user preferences from AgentCore Memory and generates personalized greeting."""
    
    def __init__(self):
        self.memory_client = boto3.client('bedrock-agentcore')
        self.memory_id = os.getenv('MEMORY_ID')
    
    def greet(self, user_id: str, phone: str) -> str:
        """Generate personalized greeting with user preferences from long-term memory."""
        if not self.memory_id:
            return f"👋 Welcome! I'm your restaurant booking assistant."
        
        # Fetch long-term preferences
        preferences = self._fetch_user_preferences(user_id)
        
        # Build greeting
        greeting_parts = [f"👋 Welcome back, {user_id}!"]
        
        if preferences:
            greeting_parts.append("\n\n📋 Your Preferences:")
            for key, value in preferences.items():
                greeting_parts.append(f"  • {key}: {value}")
            greeting_parts.append("\n\nHow can I help you today?")
        else:
            greeting_parts.append("\n\nI'm your restaurant booking assistant. How can I help you today?")
        
        return "".join(greeting_parts)
    
    def _fetch_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Fetch user preferences from AgentCore Memory long-term storage."""
        try:
            response = self.memory_client.retrieve_memory_records(
                memoryId=self.memory_id,
                namespace=f"/restaurant-booking/{user_id}/preferences",
                searchCriteria={'searchQuery': user_id},
                maxResults=10
            )
            
            # Extract preferences from memory records
            preferences = {}
            for record in response.get('memoryRecords', []):
                content = record.get('content', {}).get('text', '')
                # Parse preference format: "User prefers Italian cuisine"
                if 'prefers' in content.lower():
                    parts = content.split('prefers')
                    if len(parts) == 2:
                        key = parts[1].split(':')[0].strip()
                        preferences[key] = parts[1].strip()
            
            return preferences
        except Exception as e:
            print(f"[DEBUG] Preference fetch error: {e}")
            return {}
