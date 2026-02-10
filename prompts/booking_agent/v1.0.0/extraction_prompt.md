Extract booking parameters from the current message AND conversation history.
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
}

IMPORTANT: Check conversation history for previously mentioned information like name, phone, guests.
