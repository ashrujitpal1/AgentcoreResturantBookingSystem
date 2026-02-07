from utils import validate_guests

def calculate_token_amount(no_of_guests, meal_type='Dinner', restaurant_tier='standard'):
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
    """MCP Tool: Calculate token amount (deterministic)"""
    try:
        no_of_guests = event.get('noOfGuests')
        
        if not no_of_guests:
            return {'error': 'noOfGuests is required'}
        
        is_valid, error = validate_guests(int(no_of_guests))
        if not is_valid:
            return {'error': error}
        
        meal_type = event.get('mealType', 'Dinner')
        restaurant_tier = event.get('restaurantTier', 'standard')
        
        calculation = calculate_token_amount(int(no_of_guests), meal_type, restaurant_tier)
        
        return {
            'tokenAmount': calculation['finalAmount'],
            'calculation': calculation
        }
        
    except Exception as e:
        return {'error': str(e)}
