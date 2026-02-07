from utils import validate_guests, check_idempotency, store_idempotency

CACHE_TTL_HOURS = 24  # 24-hour cache for deterministic calculations

def calculate_token_amount(no_of_guests, meal_type='Dinner', restaurant_tier='standard'):
    """Pure deterministic calculation"""
    base_amount_per_guest = {'Breakfast': 15.0, 'Lunch': 25.0, 'Dinner': 35.0}
    tier_multiplier = {'budget': 0.8, 'standard': 1.0, 'premium': 1.5, 'luxury': 2.0}
    group_discount = {1: 0.0, 2: 0.05, 3: 0.10, 4: 0.10, 5: 0.15, 6: 0.15, 7: 0.20, 8: 0.20}
    
    base_per_guest = base_amount_per_guest.get(meal_type, 25.0)
    tier_mult = tier_multiplier.get(restaurant_tier.lower(), 1.0)
    base_total = no_of_guests * base_per_guest * tier_mult
    discount_rate = group_discount.get(no_of_guests, 0.20)
    discount_amount = base_total * discount_rate
    final_amount = max(base_total - discount_amount, 10.0)
    
    return {
        'baseAmount': round(base_total, 2),
        'discountRate': discount_rate,
        'discountAmount': round(discount_amount, 2),
        'finalAmount': round(final_amount, 2),
        'perGuestAmount': round(final_amount / no_of_guests, 2)
    }

def lambda_handler(event, context):
    """MCP Tool: Calculate token amount (deterministic) with caching"""
    try:
        # Optional requestId for caching and observability
        request_id = event.get('requestId')
        if request_id:
            cached = check_idempotency(request_id)
            if cached:
                print(f"Returning cached result for requestId: {request_id}")
                return cached
        
        no_of_guests = event.get('noOfGuests')
        
        if not no_of_guests:
            return {'error': 'noOfGuests is required'}
        
        is_valid, error = validate_guests(int(no_of_guests))
        if not is_valid:
            return {'error': error}
        
        meal_type = event.get('mealType', 'Dinner')
        restaurant_tier = event.get('restaurantTier', 'standard')
        
        calculation = calculate_token_amount(int(no_of_guests), meal_type, restaurant_tier)
        
        result = {
            'tokenAmount': calculation['finalAmount'],
            'calculation': calculation
        }
        
        # Cache result if requestId provided (deterministic, can cache long)
        if request_id:
            store_idempotency(request_id, result, ttl_hours=CACHE_TTL_HOURS)
        
        return result
        
    except Exception as e:
        print(f"Error in tokenAmountCalculation: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
