import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the budget_service directory to path so we can import flights_client
budget_service_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'budget_service')
sys.path.insert(0, budget_service_path)

from flights_client import get_amadeus_token, get_flight_offers

class TestFlightsClient(unittest.TestCase):
    
    @patch('flights_client.requests.post')
    def test_get_amadeus_token_success(self, mock_post):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_token_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Act
        token = get_amadeus_token("test_key", "test_secret")
        
        # Assert
        self.assertEqual(token, "test_token_123")
        mock_post.assert_called_once_with(
            "https://test.api.amadeus.com/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "test_key",
                "client_secret": "test_secret"
            }
        )
    
    @patch('flights_client.get_amadeus_token')
    @patch('flights_client.requests.post')
    def test_get_flight_offers_success(self, mock_post, mock_token):
        # Arrange
        mock_token.return_value = "mocked_access_token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": "1", "price": {"total": "500.00"}},
                {"id": "2", "price": {"total": "600.00"}}
            ]
        }
        mock_post.return_value = mock_response
        
        # Act
        result = get_flight_offers("YYZ", "BKK", "2025-12-10", "2025-12-15", "api_key", "api_secret")
        
        # Assert
        self.assertIn("data", result)
        self.assertEqual(len(result["data"]), 2)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://test.api.amadeus.com/v2/shopping/flight-offers")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer mocked_access_token")
        self.assertEqual(kwargs["json"]["currencyCode"], "CAD")


if __name__ == "__main__":
    unittest.main()