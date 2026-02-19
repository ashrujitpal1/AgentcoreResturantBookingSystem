"""
Intent Classifier Agent - Routes user queries to specialist agents.
Uses Nova Micro for 97% cost reduction on simple classification tasks.
"""
import json
from typing import Dict, Any, Optional
from src.core import Agent, AgentResponse, CostOptimizedModelRouter, get_prompt_manager


class IntentClassifierAgent(Agent):
    """
    Single Responsibility: Classify user intent ONLY.
    Does NOT handle actual restaurant search or booking.
    """
    
    def __init__(self, prompt_version: str = "1.0.0"):
        # Get cost-optimized providers for intent classification
        primary, fallback, breaker, config = CostOptimizedModelRouter.get_providers_for_task(
            "intent_classification"
        )
        
        # Disable guardrail for intent classifier - it blocks legitimate booking requests
        super().__init__(
            name="intent_classifier",
            primary_provider=primary,
            fallback_provider=fallback,
            circuit_breaker=breaker,
            guardrail_id=None
        )
        
        self.config = config
        self.prompt_version = prompt_version
        self.prompt_manager = get_prompt_manager()
    
    def process(
        self,
        user_message: str,
        correlation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify user intent into: search | booking | history | payment
        
        Returns:
            {
                "intent": str,
                "confidence": float,
                "extracted_entities": dict,
                "next_agent": str
            }
        """
        # Validate input for prompt injection
        is_valid, error = self.validate_input(user_message)
        if not is_valid:
            return {
                "intent": "error",
                "confidence": 0.0,
                "error": error
            }
        
        # Load versioned system prompt from S3
        system_prompt = self.prompt_manager.load_prompt(
            "intent_classifier",
            self.prompt_version
        )
        
        # Wrap user input to prevent injection
        wrapped_input = self.wrap_user_input(user_message)
        
        # Add full conversation history if available
        if context and context.get("conversation_history"):
            wrapped_input = f"{context['conversation_history']}\n\nUser: {wrapped_input}"
        
        print(f"[DEBUG] Intent Classifier - Input to LLM: {wrapped_input[:300]}...")
        
        # Invoke LLM with circuit breaker
        messages = [{"role": "user", "content": [{"text": wrapped_input}]}]
        
        response = self.invoke_llm(
            messages=messages,
            system_prompt=system_prompt,
            temperature=self.config["temperature"],
            max_tokens=self.config["max_tokens"]
        )
        
        print(f"[DEBUG] Intent Classifier - LLM Response: {response['content'][:200]}...")
        
        # Parse JSON response
        try:
            # Strip markdown code blocks if present
            content = response["content"].strip()
            if content.startswith("```"):
                # Remove ```json and ``` markers
                content = content.split("\n", 1)[1] if "\n" in content else content
                content = content.rsplit("```", 1)[0] if "```" in content else content
                content = content.strip()
            
            result = json.loads(content)
            
            # Map intent to next agent
            intent_to_agent = {
                "search": "restaurant_finder",
                "booking": "booking_agent",
                "history": "memory_agent",
                "payment": "booking_agent"
            }
            
            result["next_agent"] = intent_to_agent.get(result["intent"], "restaurant_finder")
            result["cost"] = self.calculate_cost(response["usage"])
            result["model"] = response["model"]
            
            return result
            
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            return {
                "intent": "search",
                "confidence": 0.5,
                "extracted_entities": {},
                "next_agent": "restaurant_finder",
                "error": "Failed to parse LLM response"
            }
