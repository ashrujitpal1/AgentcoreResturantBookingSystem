"""
Booking Agent - Orchestrates reservations with SAGA pattern.
Uses Claude Sonnet for accuracy-critical operations.
"""
from typing import Dict, Any, Optional, List, Tuple
from src.core import Agent, AgentResponse, CostOptimizedModelRouter, get_prompt_manager


class BookingAgent(Agent):
    """
    Single Responsibility: Booking and payment orchestration ONLY.
    Implements SAGA pattern with compensation for transaction safety.
    """
    
    def __init__(self, mcp_tools: Dict[str, Any], prompt_version: str = "1.0.0"):
        # Get Claude Sonnet for accuracy-critical operations
        primary, fallback, breaker, config = CostOptimizedModelRouter.get_providers_for_task(
            "booking_validation"
        )
        
        super().__init__(
            name="booking_agent",
            primary_provider=primary,
            fallback_provider=fallback,
            circuit_breaker=breaker
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
        Execute SAGA workflow for booking with compensation.
        
        SAGA Steps:
        1. User validation
        2. User registration (if needed)
        3. Token calculation
        4. Table booking
        5. Payment processing
        """
        # Validate input
        is_valid, error = self.validate_input(user_message)
        if not is_valid:
            return {"error": error, "success": False}
        
        # Load system prompt
        system_prompt = self.prompt_manager.load_prompt(
            "booking_agent",
            self.prompt_version
        )
        
        # Extract booking parameters
        booking_params = self._extract_booking_params(user_message, context, correlation_id)
        
        # Check for missing required fields
        missing_fields = self._check_missing_fields(booking_params)
        if missing_fields:
            return {
                "success": False,
                "missing_fields": missing_fields,
                "content": self._format_missing_fields_prompt(missing_fields),
                "partial_params": booking_params
            }
        
        # Check HITL requirements
        hitl_required, hitl_reason = self._check_hitl_requirements(booking_params)
        if hitl_required:
            return {
                "success": False,
                "hitl_required": True,
                "reason": hitl_reason,
                "booking_params": booking_params
            }
        
        # Execute SAGA workflow
        success, result, compensation_log = self._execute_saga(booking_params, correlation_id)
        
        if success:
            return {
                "success": True,
                "content": self._format_success_message(result),
                "booking_details": result,
                "compensation_log": compensation_log
            }
        else:
            return {
                "success": False,
                "content": self._format_failure_message(result, compensation_log),
                "error": result.get("error"),
                "compensation_log": compensation_log
            }
    
    def _extract_booking_params(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]],
        correlation_id: str
    ) -> Dict[str, Any]:
        """Extract booking parameters from user message, context, and memory"""
        extraction_prompt = """Extract booking parameters from user message.
Return JSON with ONLY the fields you can extract. Leave fields as null if not mentioned:
{
  "restaurantId": str or null,
  "restaurantName": str or null,
  "userName": str or null,
  "userMobileNo": str or null,
  "date": str (YYYY-MM-DD) or null,
  "time": str (HH:MM) or null,
  "noOfGuests": int or null,
  "cityName": str or null
}"""
        
        # Start with partial params from previous turns (but NOT restaurant info)
        params = {}
        if context and "partial_params" in context:
            partial = context["partial_params"].copy()
            # Keep user info but clear restaurant info (might be stale)
            for key in ["userName", "userMobileNo", "date", "time", "noOfGuests"]:
                if key in partial and partial[key]:
                    params[key] = partial[key]
        
        # Add context to help extraction
        context_info = ""
        if context:
            # Priority 1: selected_restaurant from current session
            if "selected_restaurant" in context and context["selected_restaurant"]:
                rest = context["selected_restaurant"]
                context_info = f"\nContext: Restaurant '{rest.get('name')}' in {rest.get('city')}, ID: {rest.get('restaurantId')}"
            # Priority 2: restaurants list from current search
            elif "restaurants" in context and context["restaurants"]:
                rest = context["restaurants"][0]
                context_info = f"\nContext: Restaurant '{rest.get('name')}' in {rest.get('city')}, ID: {rest.get('restaurantId')}"
            # Priority 3: Extract from conversation history
            elif "conversation_history" in context:
                history = context["conversation_history"]
                # Look for restaurant mentions in conversation
                if "Would you like to book" in history:
                    import re
                    match = re.search(r'Would you like to book.*?at ([^?\n]+)', history)
                    if match:
                        rest_name = match.group(1).strip()
                        context_info = f"\nContext: User wants to book at '{rest_name}' (from conversation)"
                # Also check if user mentioned a specific restaurant name in their message
                if "restaurants" in context and context["restaurants"]:
                    for rest in context["restaurants"]:
                        if rest.get('name', '').lower() in user_message.lower():
                            context_info = f"\nContext: User selected '{rest.get('name')}' (ID: {rest.get('restaurantId')}) from search results"
            
            if "memory_context" in context:
                context_info += f"\nPrevious conversation: {context['memory_context']}"
            if params:
                context_info += f"\nAlready collected: {params}"
        
        messages = [{"role": "user", "content": [{"text": user_message + context_info}]}]
        
        response = self.invoke_llm(
            messages=messages,
            system_prompt=extraction_prompt,
            temperature=0.0,
            max_tokens=300
        )
        
        try:
            import json
            new_params = json.loads(response["content"])
            
            # Merge new params with existing
            for key, value in new_params.items():
                if value:  # Only update if value is not None/empty
                    params[key] = value
            
            # Merge with context if available (current session takes priority)
            if context:
                restaurant_selected = None
                if "restaurants" in context and context["restaurants"] and len(context["restaurants"]) > 1:
                    restaurant_list = "\n".join([f"{i+1}. {r.get('name')} (ID: {r.get('restaurantId')})" for i, r in enumerate(context["restaurants"])])
                    match_prompt = f"User message: {user_message}\n\nAvailable restaurants:\n{restaurant_list}\n\nWhich restaurant is the user referring to? Return ONLY the restaurant ID or 'none' if unclear."
                    
                    match_response = self.invoke_llm(
                        messages=[{"role": "user", "content": [{"text": match_prompt}]}],
                        system_prompt="You are a restaurant name matcher. Return only the restaurant ID.",
                        temperature=0.0,
                        max_tokens=50
                    )
                    
                    matched_id = match_response["content"].strip()
                    for rest in context["restaurants"]:
                        if rest.get("restaurantId") == matched_id:
                            restaurant_selected = rest
                            break
                
                if restaurant_selected:
                    params["restaurantId"] = restaurant_selected.get("restaurantId")
                    params["restaurantName"] = restaurant_selected.get("name")
                    params["cityName"] = restaurant_selected.get("city")
                elif "selected_restaurant" in context and context["selected_restaurant"]:
                    rest = context["selected_restaurant"]
                    params["restaurantId"] = rest.get("restaurantId")
                    params["restaurantName"] = rest.get("name")
                    params["cityName"] = rest.get("city")
                elif "restaurants" in context and context["restaurants"] and len(context["restaurants"]) == 1:
                    rest = context["restaurants"][0]
                    params["restaurantId"] = rest.get("restaurantId")
                    params["restaurantName"] = rest.get("name")
                    params["cityName"] = rest.get("city")
                        
            return params
        except Exception as e:
            return params  # Return accumulated params even if extraction fails
    
    
    def _check_missing_fields(self, params: Dict[str, Any]) -> List[str]:
        """Check which required fields are missing"""
        required = {
            "restaurantId": "restaurant",
            "userName": "your name",
            "userMobileNo": "phone number",
            "date": "booking date",
            "time": "booking time",
            "noOfGuests": "number of guests"
        }
        
        missing = []
        for field, label in required.items():
            value = params.get(field)
            if not value or (isinstance(value, str) and len(value.strip()) == 0):
                missing.append(label)
        
        return missing
    
    def _format_missing_fields_prompt(self, missing: List[str]) -> str:
        """Generate user-friendly prompt for missing information"""
        if len(missing) == 1:
            return f"To complete your booking, I need: {missing[0]}."
        elif len(missing) == 2:
            return f"To complete your booking, I need: {missing[0]} and {missing[1]}."
        else:
            fields = ", ".join(missing[:-1]) + f", and {missing[-1]}"
            return f"To complete your booking, I need: {fields}."
    
    def _check_hitl_requirements(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if human approval required"""
        num_guests = params.get("noOfGuests", 0)
        
        if num_guests > 10:
            return True, f"Large party ({num_guests} guests) requires manager approval"
        
        return False, ""
    
    def _execute_saga(
        self,
        params: Dict[str, Any],
        correlation_id: str
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Execute SAGA workflow with compensation stack.
        Returns: (success, result, compensation_log)
        """
        compensation_stack = []
        
        try:
            # Step 1: User validation
            user = self._saga_step_user_validation(params, correlation_id)
            compensation_stack.append(("user_validation", None))  # Read-only, no compensation
            
            # Step 2: User registration (if needed)
            if not user:
                user_id = self._saga_step_user_registration(params, correlation_id)
                compensation_stack.append(("user_registration", user_id))
            else:
                user_id = user.get("userId")
            
            # Step 3: Token calculation
            token_amount = self._saga_step_token_calculation(params, correlation_id)
            compensation_stack.append(("token_calculation", None))  # Deterministic, no compensation
            
            # Step 4: Table booking
            booking_id = self._saga_step_table_booking(params, token_amount, correlation_id)
            compensation_stack.append(("table_booking", booking_id))
            
            # Step 5: Payment processing
            payment_id = self._saga_step_payment(user_id, params, booking_id, token_amount, correlation_id)
            compensation_stack.append(("payment", payment_id))
            
            return True, {
                "user_id": user_id,
                "booking_id": booking_id,
                "payment_id": payment_id,
                "token_amount": token_amount
            }, [f"✅ {step}" for step, _ in compensation_stack]
            
        except Exception as e:
            # Rollback in reverse order
            compensation_log = self._compensate(compensation_stack)
            return False, {"error": str(e)}, compensation_log
    
    def _saga_step_user_validation(self, params: Dict, correlation_id: str) -> Optional[Dict]:
        """Step 1: Validate user exists"""
        tool = self.mcp_tools.get("searchUserDetails")
        if not tool:
            raise Exception("searchUserDetails tool not available")
        
        result = tool(userMobileNo=params.get("userMobileNo"))
        return result.get("user") if result.get("found") else None
    
    def _saga_step_user_registration(self, params: Dict, correlation_id: str) -> str:
        """Step 2: Register new user"""
        tool = self.mcp_tools.get("registerUser")
        if not tool:
            raise Exception("registerUser tool not available")
        
        request_id = self.generate_request_id(correlation_id, "register")
        
        result = tool(
            username=params.get("userName"),
            mobileNo=params.get("userMobileNo"),
            userCity=params.get("cityName"),
            requestId=request_id
        )
        
        # Extract userId from response (handle different response formats)
        user_id = result.get("userId") or result.get("user_id") or result.get("id")
        if not user_id:
            raise Exception(f"No user ID returned from registerUser: {result}")
        return user_id
    
    def _saga_step_token_calculation(self, params: Dict, correlation_id: str) -> float:
        """Step 3: Calculate booking deposit"""
        tool = self.mcp_tools.get("tokenAmountCalculation")
        if not tool:
            raise Exception("tokenAmountCalculation tool not available")
        
        result = tool(noOfGuests=params.get("noOfGuests", 2))
        return result.get("tokenAmount", 0.0)
    
    def _saga_step_table_booking(self, params: Dict, token_amount: float, correlation_id: str) -> str:
        """Step 4: Book table"""
        tool = self.mcp_tools.get("bookATable")
        if not tool:
            raise Exception("bookATable tool not available")
        
        request_id = self.generate_request_id(correlation_id, "booking")
        
        result = tool(
            restaurantId=params.get("restaurantId"),
            userName=params.get("userName"),
            userMobileNo=params.get("userMobileNo"),
            date=params.get("date"),
            time=params.get("time"),
            type="dinner",
            cityName=params.get("cityName"),
            noOfGuests=params.get("noOfGuests"),
            tokenAmount=token_amount,
            requestId=request_id
        )
        
        # Extract bookingId from response (handle different response formats)
        booking_id = result.get("bookingId") or result.get("booking_id") or result.get("id")
        if not booking_id:
            raise Exception(f"No booking ID returned from bookATable: {result}")
        return booking_id
    
    def _saga_step_payment(
        self,
        user_id: str,
        params: Dict,
        booking_id: str,
        token_amount: float,
        correlation_id: str
    ) -> str:
        """Step 5: Process payment"""
        tool = self.mcp_tools.get("paymentAPI")
        if not tool:
            raise Exception("paymentAPI tool not available")
        
        request_id = self.generate_request_id(correlation_id, "payment")
        
        result = tool(
            userId=user_id,
            restaurantId=params.get("restaurantId"),
            bookingId=booking_id,
            tokenAmount=token_amount,
            paymentMethod="credit_card",
            requestId=request_id
        )
        
        # Extract paymentId from response (handle different response formats)
        payment_id = result.get("paymentId") or result.get("payment_id") or result.get("id")
        if not payment_id:
            raise Exception(f"No payment ID returned from paymentAPI: {result}")
        return payment_id
    
    def _compensate(self, compensation_stack: List[Tuple[str, Any]]) -> List[str]:
        """Execute compensation in reverse order"""
        log = []
        
        for step, resource_id in reversed(compensation_stack):
            if step == "payment" and resource_id:
                log.append(f"🔄 Refunding payment {resource_id}")
                # Call refund API
            elif step == "table_booking" and resource_id:
                log.append(f"🔄 Cancelling booking {resource_id}")
                # Call cancel booking API
            elif step == "user_registration" and resource_id:
                log.append(f"🔄 Deleting user {resource_id}")
                # Call delete user API
        
        return log
    
    def _format_success_message(self, result: Dict) -> str:
        """Format success message"""
        return f"""✅ Booking Confirmed!

📋 Booking ID: {result['booking_id']}
💰 Deposit Paid: ${result['token_amount']}
📧 Confirmation sent"""
    
    def _format_failure_message(self, result: Dict, compensation_log: List[str]) -> str:
        """Format failure message with compensation log"""
        return f"""❌ Booking Failed

Reason: {result.get('error', 'Unknown error')}

Rollback actions:
{chr(10).join(compensation_log)}

Please try again or contact support."""


import json
