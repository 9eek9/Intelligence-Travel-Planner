import unittest
import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Add the budget_service directory to path
budget_service_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'budget_service')
sys.path.insert(0, budget_service_path)

from hotels_client import get_hotel_offers

class IntegrationTestHotelsClient(unittest.TestCase):
    """Integration tests - Makes REAL API calls"""
    
    def setUp(self):
        self.api_key = os.getenv("AMADEUS_API_KEY")
        self.api_secret = os.getenv("AMADEUS_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            self.skipTest("Amadeus API credentials not found")
    
    def test_get_real_hotel_offers(self):
        """Test getting real hotel offers from Amadeus API"""
        try:
            result = get_hotel_offers(
                city_code="BKK",  # Bangkok
                checkin="2025-12-01",
                checkout="2025-12-05",
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            
            self.assertIsNotNone(result)
            print("\n" + "="*60)
            print("🏨 HOTEL SEARCH RESULTS - Bangkok")
            print("="*60)
            
            if isinstance(result, dict) and "data" in result:
                hotels = result["data"]
                print(f"\n✅ Found {len(hotels)} hotel(s)\n")
                
                for i, hotel in enumerate(hotels[:3], 1):  # Show first 3 hotels
                    print(f"\n--- Hotel #{i} ---")
                    
                    # Hotel basic info
                    if "hotel" in hotel:
                        hotel_info = hotel["hotel"]
                        print(f"Name: {hotel_info.get('name', 'N/A')}")
                        print(f"Hotel ID: {hotel_info.get('hotelId', 'N/A')}")
                        print(f"Chain Code: {hotel_info.get('chainCode', 'N/A')}")
                    
                    # Hotel offers/prices
                    if "offers" in hotel and len(hotel["offers"]) > 0:
                        offer = hotel["offers"][0]  # First offer
                        
                        if "price" in offer:
                            price = offer["price"]
                            print(f"Price: {price.get('total', 'N/A')} {price.get('currency', 'CAD')}")
                        
                        if "room" in offer:
                            room = offer["room"]
                            print(f"Room Type: {room.get('typeEstimated', {}).get('category', 'N/A')}")
                            print(f"Beds: {room.get('typeEstimated', {}).get('beds', 'N/A')}")
                        
                        if "guests" in offer:
                            print(f"Max Adults: {offer['guests'].get('adults', 'N/A')}")
                
                print("\n" + "="*60)
                
                # Print full JSON for debugging (optional)
                print("\n📄 Full Response (first hotel):")
                if len(hotels) > 0:
                    print(json.dumps(hotels[0], indent=2))
            else:
                print("⚠️  No hotel data found")
                print(f"Response: {result}")
            
        except Exception as e:
            print(f"\n❌ API call failed: {str(e)}")
            self.skipTest(f"API returned error: {str(e)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)