"""
Prompt Manager - loads versioned system prompts from S3.
Implements prompt version control with caching.
"""
import boto3
import os
from typing import Optional
from functools import lru_cache


class PromptManager:
    """
    Manages versioned system prompts stored in S3.
    Prompts are cached in memory to reduce S3 API calls.
    """
    
    def __init__(self, bucket_name: Optional[str] = None, region: str = "us-east-1"):
        self.bucket_name = bucket_name or os.getenv("PROMPT_BUCKET", "restaurant-booking-prompts")
        self.region = region
        self.s3 = boto3.client("s3", region_name=region)
    
    @lru_cache(maxsize=32)
    def load_prompt(self, agent_name: str, version: str = "1.0.0") -> str:
        """
        Load system prompt from S3 with caching.
        
        Args:
            agent_name: Name of agent (intent_classifier, restaurant_finder, booking_agent)
            version: Semantic version (default: 1.0.0)
        
        Returns:
            System prompt text
        """
        key = f"prompts/{agent_name}/v{version}/system_prompt.md"
        
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            prompt = response["Body"].read().decode("utf-8")
            return prompt
        except Exception as e:
            # Fallback to local file if S3 fails
            return self._load_local_prompt(agent_name, version)
    
    def _load_local_prompt(self, agent_name: str, version: str) -> str:
        """Fallback to local prompts directory"""
        local_path = f"prompts/{agent_name}/v{version}/system_prompt.md"
        
        try:
            with open(local_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise ValueError(f"Prompt not found: {agent_name} v{version}")
    
    def upload_prompt(self, agent_name: str, version: str, prompt_text: str):
        """Upload new prompt version to S3"""
        key = f"prompts/{agent_name}/v{version}/system_prompt.md"
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=prompt_text.encode("utf-8"),
            ContentType="text/markdown"
        )
        
        # Clear cache for this prompt
        self.load_prompt.cache_clear()
    
    def list_versions(self, agent_name: str) -> list[str]:
        """List all available versions for an agent"""
        prefix = f"prompts/{agent_name}/"
        
        response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
        
        versions = []
        for obj in response.get("Contents", []):
            # Extract version from key: prompts/agent_name/v1.0.0/system_prompt.md
            parts = obj["Key"].split("/")
            if len(parts) >= 3 and parts[2].startswith("v"):
                version = parts[2][1:]  # Remove 'v' prefix
                if version not in versions:
                    versions.append(version)
        
        return sorted(versions, reverse=True)  # Latest first


# Global instance
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """Get singleton PromptManager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
