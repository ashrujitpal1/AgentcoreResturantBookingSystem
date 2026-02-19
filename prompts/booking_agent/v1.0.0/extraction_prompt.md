Extract booking parameters from the current message AND conversation history.

The current date and time will be provided to you in the context.
When you encounter relative dates like "tomorrow", "today", "next week", you MUST:
1. Use the provided current date
2. Calculate the actual date based on the current date
3. Return the calculated date in YYYY-MM-DD format

Examples:
- If current date is 2026-02-11 and user says "tomorrow", return "2026-02-12"
- If current date is 2026-02-11 and user says "today", return "2026-02-11"
- If current date is 2026-02-11 (Tuesday) and user says "next Monday", return "2026-02-17"

Return JSON with ONLY the fields you can extract. Leave fields as null if not mentioned:
{
  "restaurantId": str or null,
  "restaurantName": str or null,
  "userName": str or null,
  "userMobileNo": str or null,
  "date": str (YYYY-MM-DD format - calculate from provided current date if relative) or null,
  "time": str (HH:MM 24-hour format) or null,
  "noOfGuests": int or null,
  "cityName": str or null
}

IMPORTANT: 
- Check conversation history for previously mentioned information like name, phone, guests.
- For relative dates: Use the provided current date to calculate the target date.
- Always return dates in YYYY-MM-DD format after calculation.
- Return ONLY valid JSON, no additional text.
