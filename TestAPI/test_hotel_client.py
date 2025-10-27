import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the budget_service directory to path
budget_service_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'budget_service')
sys.path.insert(0, budget_service_path)

from hotels_client import get_amadeus_token, get_hotel_offers

class TestHotelsClient(unittest.TestCase):
    
    @patch('hotels_client.requests.post')
    def test_get_amadeus_token_success(self, mock_post):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_token_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Act
        token = get_amadeus_token("fake_key", "fake_secret")
        
        # Assert
        self.assertEqual(token, "test_token_123")
    
    @patch('hotels_client.get_amadeus_token')
    @patch('hotels_client.requests.get')
    def test_get_hotel_offers_success(self, mock_get, mock_token):
        # Arrange
        mock_token.return_value = "mocked_access_token"
        
        # Mock hotel search response
        mock_search_response = MagicMock()
        mock_search_response.json.return_value = {
            "data": [
                {"hotelId": "HOTEL1"},
                {"hotelId": "HOTEL2"}
            ]
        }
        mock_search_response.raise_for_status = MagicMock()
        
        # Mock hotel offers response
        mock_offers_response = MagicMock()
        mock_offers_response.json.return_value = {
            "data": [
                {
                    "hotel": {"name": "Test Hotel"},
                    "offers": [{"price": {"total": "150.00", "currency": "CAD"}}]
                }
            ]
        }
        mock_offers_response.raise_for_status = MagicMock()
        
        mock_get.side_effect = [mock_search_response, mock_offers_response]
        
        # Act
        result = get_hotel_offers("BKK", "2025-12-01", "2025-12-05", "fake_key", "fake_secret")
        
        # Assert
        self.assertIn("data", result)
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('hotels_client.get_amadeus_token')
    @patch('hotels_client.requests.get')
    def test_get_hotel_offers_no_hotels(self, mock_get, mock_token):
        # Arrange
        mock_token.return_value = "mocked_access_token"
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Act
        result = get_hotel_offers("XXX", "2025-12-01", "2025-12-05", "fake_key", "fake_secret")
        
        # Assert
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)