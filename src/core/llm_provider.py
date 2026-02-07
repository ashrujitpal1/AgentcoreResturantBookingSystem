"""
LLM Provider abstraction following Open/Closed and Liskov Substitution principles.
Enables seamless switching between Bedrock models with circuit breaker support.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import boto3
from datetime import datetime


class LLMProvider(ABC):
    """Abstract base class for LLM providers (Open/Closed Principle)"""
    
    def __init__(self, model_id: str, region: str = "us-east-1"):
        self.model_id = model_id
        self.region = region
        self.bedrock = boto3.client("bedrock-runtime", region_name=region)
    
    @abstractmethod
    def invoke(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Invoke LLM with messages. Returns standardized response."""
        pass
    
    @abstractmethod
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        """Return input/output cost per 1K tokens"""
        pass


class AmazonNovaProvider(LLMProvider):
    """Amazon Nova model provider (Micro, Lite, Pro)"""
    
    COST_MATRIX = {
        "amazon.nova-micro-v1:0": {"input": 0.000035, "output": 0.00014},
        "amazon.nova-lite-v1:0": {"input": 0.00006, "output": 0.00024},
        "amazon.nova-pro-v1:0": {"input": 0.0008, "output": 0.0032}
    }
    
    def invoke(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        guardrail_id: Optional[str] = None,
        guardrail_version: str = "DRAFT",
        **kwargs
    ) -> Dict[str, Any]:
        request = {
            "messages": messages,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": max_tokens
            }
        }
        
        if system_prompt:
            request["system"] = [{"text": system_prompt}]
        
        if guardrail_id:
            request["guardrailConfig"] = {
                "guardrailIdentifier": guardrail_id,
                "guardrailVersion": guardrail_version
            }
        
        response = self.bedrock.converse(
            modelId=self.model_id,
            **request
        )
        
        return {
            "content": response["output"]["message"]["content"][0]["text"],
            "usage": response["usage"],
            "model": self.model_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        return self.COST_MATRIX.get(self.model_id, {"input": 0, "output": 0})


class AnthropicProvider(LLMProvider):
    """Anthropic Claude model provider"""
    
    COST_MATRIX = {
        "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 0.003, "output": 0.015},
        "anthropic.claude-3-5-haiku-20241022-v1:0": {"input": 0.001, "output": 0.005}
    }
    
    def invoke(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        guardrail_id: Optional[str] = None,
        guardrail_version: str = "DRAFT",
        **kwargs
    ) -> Dict[str, Any]:
        request = {
            "messages": messages,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": max_tokens
            }
        }
        
        if system_prompt:
            request["system"] = [{"text": system_prompt}]
        
        if guardrail_id:
            request["guardrailConfig"] = {
                "guardrailIdentifier": guardrail_id,
                "guardrailVersion": guardrail_version
            }
        
        response = self.bedrock.converse(
            modelId=self.model_id,
            **request
        )
        
        return {
            "content": response["output"]["message"]["content"][0]["text"],
            "usage": response["usage"],
            "model": self.model_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        return self.COST_MATRIX.get(self.model_id, {"input": 0, "output": 0})


class CircuitBreaker:
    """Circuit breaker for LLM fallback (primary fails → secondary)"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN
    
    def call(self, primary_fn, fallback_fn, *args, **kwargs):
        """Execute primary, fallback to secondary on failure"""
        
        # Circuit OPEN - use fallback
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                return fallback_fn(*args, **kwargs)
        
        # Try primary
        try:
            result = primary_fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            
            # Use fallback
            if self.state == "OPEN":
                return fallback_fn(*args, **kwargs)
            raise
    
    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def _should_attempt_reset(self) -> bool:
        if not self.last_failure_time:
            return False
        
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout


class LLMProviderFactory:
    """Factory for creating LLM providers with circuit breaker"""
    
    @staticmethod
    def create_with_fallback(
        primary_model: str,
        fallback_model: str,
        region: str = "us-east-1"
    ) -> tuple[LLMProvider, LLMProvider, CircuitBreaker]:
        """Create primary and fallback providers with circuit breaker"""
        
        primary = LLMProviderFactory._create_provider(primary_model, region)
        fallback = LLMProviderFactory._create_provider(fallback_model, region)
        circuit_breaker = CircuitBreaker()
        
        return primary, fallback, circuit_breaker
    
    @staticmethod
    def _create_provider(model_id: str, region: str) -> LLMProvider:
        if "nova" in model_id:
            return AmazonNovaProvider(model_id, region)
        elif "claude" in model_id:
            return AnthropicProvider(model_id, region)
        else:
            raise ValueError(f"Unsupported model: {model_id}")
