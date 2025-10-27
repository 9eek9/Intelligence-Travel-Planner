import os
import json
from dotenv import load_dotenv
from hotels_client import get_hotel_offers

load_dotenv()

api_key = os.getenv("AMADEUS_API_KEY")
api_secret = os.getenv("AMADEUS_API_SECRET")

print("🔍 Fetching hotel data to inspect structure...\n")
result = get_hotel_offers("BKK", "2025-12-01", "2025-12-05", api_key, api_secret)

print(f"Response keys: {result.keys()}")
print(f"Number of hotels: {len(result.get('data', []))}")

if result.get('data'):
    print(f"\n📄 First hotel complete structure:\n")
    print(json.dumps(result['data'][0], indent=2))
    
    print(f"\n📄 Second hotel (if exists):\n")
    if len(result['data']) > 1:
        print(json.dumps(result['data'][1], indent=2))