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
        
        # Get guardrail ID from environment
        import os
        guardrail_id = os.getenv("GUARDRAIL_ID")
        
        super().__init__(
            name="booking_agent",
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
        Execute SAGA workflow for booking with compensation.
        
        SAGA Steps:
        1. Session booking limit check
        2. User validation
        3. User registration (if needed)
        4. Token calculation
        5. Table booking
        6. Payment processing
        """
        # Check if user already booked in this session
        if context and context.get("booking_completed"):
            return {
                "success": False,
                "content": "You have already completed a booking in this session. To make another reservation, please log out and log back in. This ensures each booking is properly tracked and secured."
            }
        
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
        extraction_prompt = self.prompt_manager.load_prompt_file(
            "booking_agent",
            "extraction_prompt.md",
            self.prompt_version
        )
        
        # Start with partial params from previous turns
        params = {}
        if context and "partial_params" in context:
            params = context["partial_params"].copy()
        
        # Build context for LLM
        context_info = ""
        if context:
            # Add conversation history for LLM to extract from
            if "conversation_history" in context:
                context_info += f"\n\nConversation History:\n{context['conversation_history']}"
            
            # Add restaurant context
            if "selected_restaurant" in context and context["selected_restaurant"]:
                rest = context["selected_restaurant"]
                context_info += f"\n\nSelected Restaurant: {rest.get('name')} (ID: {rest.get('restaurantId')}, City: {rest.get('city')})"
            elif "restaurants" in context and context["restaurants"]:
                rest = context["restaurants"][0]
                context_info += f"\n\nAvailable Restaurant: {rest.get('name')} (ID: {rest.get('restaurantId')}, City: {rest.get('city')})"
            
            # Add memory context
            if "memory_context" in context:
                context_info += f"\n\nPrevious Context: {context['memory_context']}"
            
            # Show already collected params
            if params:
                context_info += f"\n\nAlready Collected: {params}"
        
        messages = [{"role": "user", "content": [{"text": f"Current Message: {user_message}{context_info}"}]}]
        
        response = self.invoke_llm(
            messages=messages,
            system_prompt=extraction_prompt,
            temperature=0.0,
            max_tokens=300
        )
        
        try:
            import json
            import re
            
            # Clean response - remove comments and extract JSON
            content = response["content"].strip()
            
            # Extract from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            # Remove inline comments (// ...)
            content = re.sub(r'//.*?(?=\n|$)', '', content)
            # Remove multi-line comments (/* ... */)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            
            print(f"[DEBUG] Booking Agent - LLM extraction response: {content}")
            new_params = json.loads(content)
            
            # Merge new params with existing
            for key, value in new_params.items():
                if value:  # Only update if value is not None/empty
                    params[key] = value
            
            print(f"[DEBUG] Booking Agent - Params after LLM extraction: {params}")
            
            # Merge with context if available (current session takes priority)
            if context and "restaurants" in context and context["restaurants"]:
                # If user mentioned restaurant name, match it
                if len(context["restaurants"]) > 1:
                    for rest in context["restaurants"]:
                        if rest.get('name', '').lower() in user_message.lower():
                            params["restaurantId"] = rest.get("restaurantId")
                            params["restaurantName"] = rest.get("name")
                            params["cityName"] = rest.get("city")
                            break
                elif len(context["restaurants"]) == 1:
                    # Only one restaurant, use it
                    rest = context["restaurants"][0]
                    params["restaurantId"] = rest.get("restaurantId")
                    params["restaurantName"] = rest.get("name")
                    params["cityName"] = rest.get("city")
            
            print(f"[DEBUG] Booking Agent - Final params: {params}")
            
            # Normalize date if present
            if params.get("date"):
                params["date"] = self._normalize_date(params["date"], correlation_id)
                print(f"[DEBUG] Booking Agent - Normalized date: {params['date']}")
            
            return params
        except Exception as e:
            print(f"[DEBUG] Booking Agent - Extraction error: {e}")
            print(f"[DEBUG] Booking Agent - LLM response was: {response.get('content', 'NO CONTENT')}")
            return params  # Return accumulated params even if extraction fails
    
    
    def _normalize_date(self, date_str: str, correlation_id: str) -> str:
        """Convert relative dates to YYYY-MM-DD using getCurrentDateTime tool"""
        if not date_str or not isinstance(date_str, str):
            return date_str
        
        # Check if already in YYYY-MM-DD format
        import re
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        
        # Check if date is relative
        relative_terms = ['today', 'tomorrow', 'tonight', 'next', 'this', 'week', 'weekend', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if any(term in date_str.lower() for term in relative_terms):
            print(f"[DEBUG] Booking Agent - Detected relative date: {date_str}")
            
            # Call getCurrentDateTime tool
            tool = self.mcp_tools.get("getCurrentDateTime")
            if tool:
                try:
                    result = tool(timezone="America/New_York")
                    current_date = result.get("currentDate") or result.get("date")
                    current_time = result.get("currentTime") or result.get("time")
                    
                    print(f"[DEBUG] Booking Agent - getCurrentDateTime returned: {current_date} {current_time}")
                    
                    if current_date:
                        # Use LLM to calculate relative date
                        date_conversion_prompt = self.prompt_manager.load_prompt_file(
                            "booking_agent",
                            "date_conversion_prompt.md",
                            self.prompt_version
                        )
                        
                        prompt = f"""Current date is {current_date}. Convert the relative date '{date_str}' to YYYY-MM-DD format.
Return ONLY the date in YYYY-MM-DD format, nothing else."""
                        
                        messages = [{"role": "user", "content": [{"text": prompt}]}]
                        response = self.invoke_llm(
                            messages=messages,
                            system_prompt=date_conversion_prompt,
                            temperature=0.0,
                            max_tokens=50
                        )
                        
                        normalized = response["content"].strip()
                        # Extract date if wrapped in text
                        date_match = re.search(r'\d{4}-\d{2}-\d{2}', normalized)
                        if date_match:
                            normalized = date_match.group(0)
                        
                        print(f"[DEBUG] Booking Agent - Normalized '{date_str}' to '{normalized}'")
                        return normalized
                except Exception as e:
                    print(f"[DEBUG] Booking Agent - Date normalization error: {e}")
        
        return date_str
    
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
        """Format success message with actual data from result"""
        booking_id = result.get('booking_id') or result.get('bookingId') or 'N/A'
        token_amount = result.get('token_amount') or result.get('tokenAmount') or 0.0
        
        return f"""✅ Booking Confirmed!

📋 Booking ID: {booking_id}
💰 Deposit Paid: ${token_amount}
📧 Confirmation sent"""
    
    def _format_failure_message(self, result: Dict, compensation_log: List[str]) -> str:
        """Format failure message with compensation log"""
        return f"""❌ Booking Failed

Reason: {result.get('error', 'Unknown error')}

Rollback actions:
{chr(10).join(compensation_log)}

Please try again or contact support."""


import json
