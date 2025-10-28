import requests

def convert_currency(amount, from_currency, to_currency, api_key=None, timeout=10):
    """
    Convert currency using exchangerate-api.com
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., 'USD')
        to_currency: Target currency code (e.g., 'CAD')
        api_key: Optional API key for exchangerate-api.com (if None, uses free v4 API)
        timeout: Request timeout in seconds
    
    Returns:
        float: Converted amount
    
    Raises:
        ValueError: If currency codes are invalid or API returns error
        requests.exceptions.RequestException: If API request fails
    """
    # Validate inputs
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    if not from_currency or not to_currency:
        raise ValueError("Currency codes cannot be empty")
    
    # Choose API endpoint based on whether API key is provided
    if api_key:
        # v6 API with API key (requires sign-up at exchangerate-api.com)
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{from_currency}"
    else:
        # v4 API without API key (free, but limited)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
    
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API errors (v6 returns 'result' field)
        if api_key and data.get("result") != "success":
            error_type = data.get("error-type", "Unknown error")
            raise ValueError(f"API error: {error_type}")
        
        # Check if target currency exists in rates
        if to_currency not in data.get("conversion_rates", data.get("rates", {})):
            raise ValueError(f"Currency code '{to_currency}' not found")
        
        # Calculate converted amount (v6 uses 'conversion_rates', v4 uses 'rates')
        rates = data.get("conversion_rates", data.get("rates", {}))
        exchange_rate = rates[to_currency]
        converted_amount = amount * exchange_rate
        
        return round(converted_amount, 2)
        
    except requests.exceptions.Timeout:
        raise requests.exceptions.RequestException("Currency conversion request timed out")
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Failed to fetch exchange rates: {str(e)}")
    except KeyError as e:
        raise ValueError(f"Unexpected API response format: {str(e)}")