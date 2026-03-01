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
        
        # Disable guardrail for restaurant finder - not needed for search operations
        super().__init__(
            name="restaurant_finder",
            primary_provider=primary,
            fallback_provider=fallback,
            circuit_breaker=breaker,
            guardrail_id=None
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
        extracted = self._extract_search_params(user_message, correlation_id, context)
        
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
    
    def _extract_search_params(self, user_message: str, correlation_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract city, cuisine, price range, rating from user message using tool schema"""
        from src.tools.mcp_gateway_client import get_mcp_client
        
        print(f"[DEBUG] Starting parameter extraction for: {user_message}")
        
        # Get tool schema dynamically
        mcp_client = get_mcp_client()
        print(f"[DEBUG] MCP client obtained, listing tools...")
        
        tools = mcp_client.list_tools_sync()
        print(f"[DEBUG] Found {len(tools)} tools")
        
        tool_schema = None
        for tool in tools:
            print(f"[DEBUG] Checking tool: {tool.tool_name}")
            if 'fetchRestaurantDetails' in tool.tool_name and 'ById' not in tool.tool_name:
                tool_schema = tool.tool_spec['inputSchema']['json']
                print(f"[DEBUG] Found matching tool schema: {tool.tool_name}")
                break
        
        if not tool_schema:
            print("[ERROR] Could not find fetchRestaurantDetails tool schema")
            return {}
        
        # Build extraction prompt with schema
        schema_desc = "\n".join([
            f"- {name}: {props.get('description', 'No description')} (type: {props.get('type')})"
            for name, props in tool_schema['properties'].items()
            if name not in ['requestId', 'maxResults', 'nextToken']  # Skip internal fields
        ])
        
        conversation_history = context.get("conversation_history", "") if context else ""
        prior_search = context.get("search_criteria", {}) if context else {}

        context_block = ""
        if conversation_history:
            context_block = f"\nConversation so far:\n{conversation_history}\n"
        if prior_search:
            context_block += f"\nPrevious search criteria: {prior_search}\n"

        extraction_prompt = f"""Extract restaurant search parameters from the user message, using conversation context to resolve references like "same city" or "that area".

Available parameters:
{schema_desc}
{context_block}
User message: {user_message}

Return ONLY a JSON object with the extracted parameters. Omit parameters not mentioned.
Examples:
- "Find Italian in Boston" → {{"city": "Boston", "cuisine": "Italian"}}
- "Show Indian restaurants in New York" → {{"city": "New York", "cuisine": "Indian"}}
- "Cheap sushi" → {{"cuisine": "Japanese", "priceRange": "$"}}
- "Same city but Italian" (after searching New York) → {{"city": "New York", "cuisine": "Italian"}}

Return {{}} if no parameters found."""
        
        messages = [{"role": "user", "content": [{"text": extraction_prompt}]}]
        
        response = self.invoke_llm(
            messages=messages,
            system_prompt="You are a parameter extraction assistant. Return only valid JSON.",
            temperature=0.0,
            max_tokens=200
        )
        
        print(f"[DEBUG] LLM extraction response: {response.get('content', 'NO CONTENT')}")
        
        try:
            import re
            content = response["content"].strip()
            
            # Extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                # Try to find JSON object
                json_match = re.search(r'{[^}]+}', content)
                if json_match:
                    content = json_match.group(0)
            
            parsed = json.loads(content)
            print(f"[DEBUG] Parsed params: {parsed}")
            return parsed
        except Exception as e:
            print(f"[DEBUG] Extraction error: {e}, returning empty dict")
            return {}
    
    def _fetch_restaurants(self, params: Dict[str, Any], correlation_id: str) -> List[Dict]:
        """Call MCP tool to fetch restaurants"""
        from src.tools.mcp_gateway_client import get_mcp_client
        
        request_id = self.generate_request_id(correlation_id, "search")
        mcp_client = get_mcp_client()
        
        # Build arguments, excluding None values
        arguments = {}
        if params.get("city"):
            arguments["city"] = params["city"]
        if params.get("cuisine"):
            arguments["cuisine"] = params["cuisine"]
        if params.get("priceRange"):
            arguments["priceRange"] = params["priceRange"]
        if params.get("minRating"):
            arguments["minRating"] = params["minRating"]
        
        print(f"[DEBUG] Calling Lambda with arguments: {arguments}")
        print(f"[DEBUG] Request ID: {request_id}")
        print(f"[DEBUG] Tool name: fetchRestaurantDetails-target-1771948384___fetchRestaurantDetails")
        
        try:
            print(f"[DEBUG] Invoking MCP tool...")
            result = mcp_client.call_tool_sync(
                name="fetchRestaurantDetails-target-1771948384___fetchRestaurantDetails",
                arguments=arguments,
                tool_use_id=request_id
            )
            
            print(f"[DEBUG] MCP tool result status: {result.get('status')}")
            print(f"[DEBUG] MCP tool result keys: {result.keys()}")
            
            # Parse MCP response - data is in content[0].text as JSON string
            if result.get('status') == 'success' and result.get('content'):
                print(f"[DEBUG] Result content length: {len(result['content'])}")
                text_content = result['content'][0].get('text', '{}')
                print(f"[DEBUG] Text content (first 200 chars): {text_content[:200]}")
                
                parsed = json.loads(text_content)
                restaurants = parsed.get('restaurants', [])
                print(f"[DEBUG] Lambda returned {len(restaurants)} restaurants")
                
                if restaurants:
                    print(f"[DEBUG] First restaurant: {restaurants[0]}")
                
                return restaurants
            else:
                print(f"[DEBUG] Lambda error or no content: {result}")
                return []
        except Exception as e:
            print(f"[ERROR] Error fetching restaurants: {e}")
            print(f"[ERROR] Error type: {type(e).__name__}")
            import traceback
            print(f"[ERROR] Full traceback:")
            traceback.print_exc()
            return []
    
    def _generate_response(
        self,
        restaurants: List[Dict],
        user_message: str,
        system_prompt: str
    ) -> str:
        """Generate conversational response with restaurant recommendations"""
        if not restaurants:
            # Use LLM to generate contextual no-results response
            prompt = f"""The user searched for restaurants but no results were found.

User request: {user_message}

Generate a helpful response that:
1. Acknowledges no restaurants were found
2. Suggests specific alternatives based on their search (try different city OR different cuisine)
3. Asks them to clarify their preference

Be conversational and helpful."""
            
            messages = [{"role": "user", "content": [{"text": prompt}]}]
            
            response = self.invoke_llm(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=150
            )
            
            return response["content"]
        
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
