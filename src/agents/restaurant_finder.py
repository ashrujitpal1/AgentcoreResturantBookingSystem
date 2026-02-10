"""
Restaurant Finder Agent - Searches and recommends restaurants.
Uses Nova Lite with Haiku fallback. Implements handoff pattern.
"""
import json
from typing import Dict, Any, Optional, List
from src.core import Agent, AgentResponse, CostOptimizedModelRouter, get_prompt_manager


class RestaurantFinderAgent(Agent):
    """
    Single Responsibility: Search and recommend restaurants ONLY.
    Does NOT handle bookings - hands off to BookingAgent.
    """
    
    def __init__(self, mcp_tools: Dict[str, Any], prompt_version: str = "1.0.0"):
        # Get cost-optimized providers
        primary, fallback, breaker, config = CostOptimizedModelRouter.get_providers_for_task(
            "restaurant_search"
        )
        
        import os
        guardrail_id = os.getenv("GUARDRAIL_ID")
        
        super().__init__(
            name="restaurant_finder",
            primary_provider=primary,
            fallback_provider=fallback,
            circuit_breaker=breaker,
            guardrail_id=guardrail_id
        )
        
        self.config = config
        self.prompt_version = prompt_version
        self.prompt_manager = get_prompt_manager()
        self.mcp_tools = mcp_tools
    
    def process(
        self,
        user_message: str,
        correlation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search restaurants and provide recommendations.
        Handoff to booking agent if user wants to book.
        """
        # Validate input
        is_valid, error = self.validate_input(user_message)
        if not is_valid:
            return {"error": error, "handoff_to": None}
        
        # Load system prompt
        system_prompt = self.prompt_manager.load_prompt(
            "restaurant_finder",
            self.prompt_version
        )
        
        # Extract search parameters using LLM
        extracted = self._extract_search_params(user_message, correlation_id)
        
        # Call MCP tool to fetch restaurants
        restaurants = self._fetch_restaurants(extracted, correlation_id)
        
        # Generate conversational response
        response_text = self._generate_response(restaurants, user_message, system_prompt)
        
        # Check for handoff trigger
        handoff_to = self._check_handoff(user_message, restaurants)
        
        return {
            "content": response_text,
            "restaurants": restaurants[:5],  # Top 5 only
            "handoff_to": handoff_to,
            "context": {
                "search_criteria": extracted,
                "result_count": len(restaurants)
            }
        }
    
    def _extract_search_params(self, user_message: str, correlation_id: str) -> Dict[str, Any]:
        """Extract city, cuisine, price range, rating from user message"""
        extraction_prompt = self.prompt_manager.load_prompt_file(
            "restaurant_finder",
            "extraction_prompt.md",
            self.prompt_version
        )
        
        messages = [{"role": "user", "content": [{"text": user_message}]}]
        
        response = self.invoke_llm(
            messages=messages,
            system_prompt=extraction_prompt,
            temperature=0.0,
            max_tokens=200
        )
        
        try:
            return json.loads(response["content"])
        except:
            return {"city": None, "cuisine": None, "priceRange": None, "minRating": None}
    
    def _fetch_restaurants(self, params: Dict[str, Any], correlation_id: str) -> List[Dict]:
        """Call MCP tool to fetch restaurants"""
        tool = self.mcp_tools.get("fetchRestaurantDetails")
        if not tool:
            return []
        
        # Generate idempotent request ID
        request_id = self.generate_request_id(correlation_id, "search")
        
        # Call tool with extracted parameters
        result = tool(
            city=params.get("city"),
            cuisine=params.get("cuisine"),
            priceRange=params.get("priceRange"),
            minRating=params.get("minRating"),
            requestId=request_id
        )
        
        return result.get("restaurants", [])
    
    def _generate_response(
        self,
        restaurants: List[Dict],
        user_message: str,
        system_prompt: str
    ) -> str:
        """Generate conversational response with restaurant recommendations"""
        if not restaurants:
            return "I couldn't find any restaurants matching your criteria. Please try a different location or cuisine type."
        
        # Format restaurants for LLM with actual data - validate all fields
        restaurants_text = "\n\n".join([
            f"{i+1}. {r.get('name', 'Unknown')} - {r.get('cuisine', 'N/A')} cuisine\n   Rating: {r.get('rating', 'N/A')}/5\n   Location: {r.get('city', 'N/A')}\n   ID: {r.get('restaurantId', 'N/A')}"
            for i, r in enumerate(restaurants[:5])
        ])
        
        # Add validation check
        if not restaurants_text.strip():
            return "I found restaurants but couldn't retrieve their details. Please try again."
        
        prompt = f"""Based on the user's request, present these restaurants in a friendly way.

CRITICAL GROUNDEDNESS RULES:
1. DO NOT make up, invent, or hallucinate ANY restaurants
2. ONLY use the exact restaurants listed below
3. DO NOT add details not present in the data (hours, menu items, prices)
4. If a field is missing, say "Not available" instead of guessing
5. Use ONLY the restaurant IDs, names, ratings, and cities provided

Restaurants found:
{restaurants_text}

User request: {user_message}

Provide a helpful response listing ONLY these restaurants with ONLY the information provided above."""
        
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        
        response = self.invoke_llm(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=self.config["max_tokens"]
        )
        
        # Validate response doesn't contain hallucinated restaurant names
        response_text = response["content"]
        actual_names = [r.get('name', '') for r in restaurants[:5]]
        
        # Log warning if response might contain hallucinations (basic check)
        for name in actual_names:
            if name and name not in response_text:
                print(f"[WARNING] Restaurant '{name}' from data not found in LLM response")
        
        return response_text
    
    def _check_handoff(self, user_message: str, restaurants: List[Dict]) -> Optional[str]:
        """Use LLM to determine if user wants to proceed with booking"""
        if not restaurants:
            return None
        
        handoff_prompt = self.prompt_manager.load_prompt_file(
            "restaurant_finder",
            "handoff_detection_prompt.md",
            self.prompt_version
        )
        
        # Ask LLM to determine intent
        handoff_prompt_content = f"""User message: {user_message}

Restaurants were just shown to the user.

Does the user want to PROCEED WITH BOOKING now?
- If user is just asking for search/recommendations → return "no"
- If user confirms/selects a restaurant to book → return "yes"

Examples:
"I want to book a table in Indian restaurant" → no (just searching)
"Yes, book Spice Symphony" → yes (confirming booking)
"I'll take the first one" → yes (selecting)
"Show me more options" → no (still searching)

Return ONLY "yes" or "no"."""
        
        messages = [{"role": "user", "content": [{"text": handoff_prompt_content}]}]
        
        response = self.invoke_llm(
            messages=messages,
            system_prompt=handoff_prompt,
            temperature=0.0,
            max_tokens=10
        )
        
        decision = response["content"].strip().lower()
        return "booking_agent" if decision == "yes" else None
