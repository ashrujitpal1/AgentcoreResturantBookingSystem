"""
Base Agent class following SOLID principles.
All specialized agents inherit from this base class.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from .llm_provider import LLMProvider, CircuitBreaker


class Agent(ABC):
    """
    Abstract base class for all agents (Single Responsibility + Open/Closed).
    Each agent handles ONE specific task only.
    """
    
    def __init__(
        self,
        name: str,
        primary_provider: LLMProvider,
        fallback_provider: Optional[LLMProvider] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        """
        Dependency Inversion: Inject LLM providers via constructor
        """
        self.name = name
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.circuit_breaker = circuit_breaker
    
    @abstractmethod
    def process(
        self,
        user_message: str,
        correlation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user message and return result.
        Each agent implements its own processing logic.
        """
        pass
    
    def invoke_llm(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Invoke LLM with circuit breaker fallback.
        Primary fails → automatically use fallback provider.
        """
        if self.circuit_breaker and self.fallback_provider:
            return self.circuit_breaker.call(
                lambda: self.primary_provider.invoke(
                    messages, system_prompt, temperature, max_tokens
                ),
                lambda: self.fallback_provider.invoke(
                    messages, system_prompt, temperature, max_tokens
                )
            )
        else:
            return self.primary_provider.invoke(
                messages, system_prompt, temperature, max_tokens
            )
    
    def generate_request_id(self, correlation_id: str, operation: str) -> str:
        """Generate idempotent request ID for tool calls"""
        return f"{correlation_id}_{operation}_{uuid.uuid4().hex[:8]}"
    
    def validate_input(self, user_message: str) -> tuple[bool, str]:
        """Validate input for prompt injection attacks"""
        INJECTION_PATTERNS = [
            r"ignore\s+(previous|all)\s+instructions?",
            r"you\s+are\s+now\s+a",
            r"disregard\s+everything",
            r"system\s*:",
            r"<\s*system\s*>"
        ]
        
        import re
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, user_message, re.IGNORECASE):
                return False, "Invalid input detected"
        
        return True, ""
    
    def wrap_user_input(self, user_message: str) -> str:
        """Wrap user input to prevent prompt injection"""
        return f"<user_input>\n{user_message}\n</user_input>"
    
    def calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage"""
        costs = self.primary_provider.get_cost_per_1k_tokens()
        input_cost = (usage.get("inputTokens", 0) / 1000) * costs["input"]
        output_cost = (usage.get("outputTokens", 0) / 1000) * costs["output"]
        return input_cost + output_cost


class AgentResponse:
    """Standardized agent response format"""
    
    def __init__(
        self,
        agent_name: str,
        correlation_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        handoff_to: Optional[str] = None
    ):
        self.agent_name = agent_name
        self.correlation_id = correlation_id
        self.content = content
        self.metadata = metadata or {}
        self.handoff_to = handoff_to
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "correlation_id": self.correlation_id,
            "content": self.content,
            "metadata": self.metadata,
            "handoff_to": self.handoff_to,
            "timestamp": self.timestamp
        }
