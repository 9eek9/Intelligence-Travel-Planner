import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the budget_service directory to path
budget_service_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'budget_service')
sys.path.insert(0, budget_service_path)

from fx_client import convert_currency

class TestFxClient(unittest.TestCase):
    
    @patch('fx_client.requests.get')
    def test_convert_currency_without_api_key(self, mock_get):
        # Arrange - v4 API response format
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "base": "USD",
            "rates": {
                "CAD": 1.35,
                "EUR": 0.85
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Act
        result = convert_currency(100, "USD", "CAD")
        
        # Assert
        self.assertEqual(result, 135.0)
        mock_get.assert_called_once_with(
            "https://api.exchangerate-api.com/v4/latest/USD",
            timeout=10
        )
    
    @patch('fx_client.requests.get')
    def test_convert_currency_with_api_key(self, mock_get):
        # Arrange - v6 API response format
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": "success",
            "base_code": "USD",
            "conversion_rates": {
                "CAD": 1.35,
                "EUR": 0.85
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Act
        result = convert_currency(100, "USD", "CAD", api_key="test_key_123")
        
        # Assert
        self.assertEqual(result, 135.0)
        mock_get.assert_called_once_with(
            "https://v6.exchangerate-api.com/v6/test_key_123/latest/USD",
            timeout=10
        )
    
    @patch('fx_client.requests.get')
    def test_convert_currency_invalid_target(self, mock_get):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "base": "USD",
            "rates": {
                "CAD": 1.35
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            convert_currency(100, "USD", "INVALID")
        
        self.assertIn("not found", str(context.exception))
    
    def test_convert_currency_negative_amount(self):
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            convert_currency(-100, "USD", "CAD")
        
        self.assertIn("positive", str(context.exception))
    
    def test_convert_currency_empty_currency(self):
        # Act & Assert
        with self.assertRaises(ValueError):
            convert_currency(100, "", "CAD")


if __name__ == "__main__":
    unittest.main(verbosity=2)