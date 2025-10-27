import unittest
import sys
import os
from dotenv import load_dotenv

# Load environment variables from parent directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Add the budget_service directory to path
budget_service_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'budget_service')
sys.path.insert(0, budget_service_path)

from flights_client import get_amadeus_token, get_flight_offers

class IntegrationTestFlightsClient(unittest.TestCase):
    
    def setUp(self):
        # Load from environment variables
        self.api_key = os.getenv("AMADEUS_API_KEY")
        self.api_secret = os.getenv("AMADEUS_API_SECRET")
        
        print(f"\nLoaded API Key: {self.api_key}")
        print(f"Loaded API Secret: {self.api_secret}")
        
        if not self.api_key or not self.api_secret:
            self.skipTest("API credentials not found in environment variables")
    
    def test_get_real_amadeus_token(self):
        """Test getting a real token from Amadeus API"""
        try:
            token = get_amadeus_token(self.api_key, self.api_secret)
            self.assertIsNotNone(token)
            self.assertIsInstance(token, str)
            print(f"✅ Token received: {token[:20]}...")
        except Exception as e:
            print(f"Error details: {str(e)}")
            self.fail(f"Failed to get token: {str(e)}")
    
    def test_get_real_flight_offers(self):
        """Test getting real flight offers from Amadeus API"""
        try:
            result = get_flight_offers(
                origin="YYZ",
                destination="JFK",
                depart_date="2025-12-01",
                return_date="2025-12-05",
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            
            self.assertIsNotNone(result)
            print(f"✅ Response: {result}")
        except Exception as e:
            print(f"Error details: {str(e)}")
            self.fail(f"Failed to get flight offers: {str(e)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)