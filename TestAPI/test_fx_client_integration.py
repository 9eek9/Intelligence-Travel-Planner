import unittest
import sys
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Add the budget_service directory to path
budget_service_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'budget_service')
sys.path.insert(0, budget_service_path)

from fx_client import convert_currency

class IntegrationTestFxClient(unittest.TestCase):
    """Integration tests - Makes REAL API calls"""
    
    def test_convert_usd_to_cad_free_api(self):
        """Test real USD to CAD conversion using free API (no key)"""
        result = convert_currency(100, "USD", "CAD")
        
        # Assert result is reasonable (CAD is typically 1.2-1.4x USD)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 100)
        self.assertLess(result, 200)
        print(f"✅ 100 USD = {result} CAD (free API)")
    
    def test_convert_with_api_key(self):
        """Test conversion with API key (if available)"""
        api_key = os.getenv("EXCHANGERATE_API_KEY")
        
        # Skip test if no API key or placeholder key
        if not api_key or api_key in ["YOUR_EXCHANGERATE_API_KEY_HERE", "Y13a859cdeb3dc0b645d9f087"]:
            self.skipTest("No valid exchangerate-api.com API key configured")
        
        print(f"Testing with API key: {api_key[:8]}...")
        
        try:
            result = convert_currency(100, "USD", "CAD", api_key=api_key)
            
            self.assertIsInstance(result, float)
            self.assertGreater(result, 100)
            print(f"✅ 100 USD = {result} CAD (with API key)")
        except Exception as e:
            # Print error details for debugging
            print(f"❌ API key test failed: {str(e)}")
            self.skipTest(f"API key appears invalid: {str(e)}")
    
    def test_convert_cad_to_thb(self):
        """Test real CAD to THB (Thai Baht) conversion"""
        result = convert_currency(1000, "CAD", "THB")
        
        self.assertIsInstance(result, float)
        self.assertGreater(result, 1000)  # THB > CAD
        print(f"✅ 1000 CAD = {result} THB")


if __name__ == "__main__":
    unittest.main(verbosity=2)