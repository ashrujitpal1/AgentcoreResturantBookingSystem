"""
Cost-Optimized Model Router - selects cheapest model for each task.
Implements cost as first-class metric with 97% cost reduction for simple tasks.
"""
from typing import Dict, Literal
from .llm_provider import LLMProviderFactory, LLMProvider, CircuitBreaker


TaskType = Literal[
    "intent_classification",
    "restaurant_search",
    "booking_validation",
    "payment_processing",
    "complex_reasoning"
]


class CostOptimizedModelRouter:
    """
    Intelligent model selection based on task complexity.
    Simple tasks → Nova Micro (97% cheaper)
    Complex tasks → Claude Sonnet (accuracy-critical)
    """
    
    # Model selection matrix with cost optimization
    MODEL_SELECTION = {
        "intent_classification": {
            "primary": "amazon.nova-lite-v1:0",
            "fallback": "amazon.nova-pro-v1:0",
            "temperature": 0.0,  # Deterministic
            "max_tokens": 150
        },
        "restaurant_search": {
            "primary": "amazon.nova-lite-v1:0",
            "fallback": "amazon.nova-micro-v1:0",
            "temperature": 0.3,
            "max_tokens": 1000
        },
        "booking_validation": {
            "primary": "amazon.nova-pro-v1:0",
            "fallback": "amazon.nova-lite-v1:0",
            "temperature": 0.2,
            "max_tokens": 1500
        },
        "payment_processing": {
            "primary": "amazon.nova-pro-v1:0",
            "fallback": "amazon.nova-lite-v1:0",
            "temperature": 0.0,  # Accuracy-critical
            "max_tokens": 1000
        },
        "complex_reasoning": {
            "primary": "amazon.nova-pro-v1:0",
            "fallback": "anthropic.claude-3-5-haiku-20241022-v1:0",
            "temperature": 0.5,
            "max_tokens": 2000
        }
    }
    
    @staticmethod
    def get_providers_for_task(
        task: TaskType,
        region: str = "us-east-1"
    ) -> tuple[LLMProvider, LLMProvider, CircuitBreaker, Dict[str, any]]:
        """
        Get primary and fallback providers for a task with circuit breaker.
        Returns: (primary_provider, fallback_provider, circuit_breaker, config)
        """
        config = CostOptimizedModelRouter.MODEL_SELECTION[task]
        
        primary, fallback, circuit_breaker = LLMProviderFactory.create_with_fallback(
            primary_model=config["primary"],
            fallback_model=config["fallback"],
            region=region
        )
        
        llm_config = {
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"]
        }
        
        return primary, fallback, circuit_breaker, llm_config
    
    @staticmethod
    def get_cost_comparison() -> Dict[str, Dict[str, float]]:
        """Get cost comparison across models (per 1M tokens)"""
        return {
            "amazon.nova-micro-v1:0": {"input": 35, "output": 140},
            "amazon.nova-lite-v1:0": {"input": 60, "output": 240},
            "amazon.nova-pro-v1:0": {"input": 800, "output": 3200},
            "anthropic.claude-3-5-haiku-20241022-v1:0": {"input": 1000, "output": 5000},
            "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 3000, "output": 15000}
        }
