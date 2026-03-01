Extract search parameters from user message.

Examples:
- "Find Italian restaurants in Boston" → {"city": "Boston", "cuisine": "Italian"}
- "Show me Indian food in New York" → {"city": "New York", "cuisine": "Indian"}
- "Cheap restaurants in Chicago" → {"city": "Chicago", "priceRange": "$"}
- "Highly rated sushi" → {"cuisine": "Japanese", "minRating": 4.5}

Return ONLY valid JSON with these fields (omit fields if not mentioned):
- city: string (city name)
- cuisine: string (cuisine type)
- priceRange: string ("$", "$$", "$$$", "$$$$")
- minRating: number (1.0 to 5.0)

Return {} if no parameters found.
