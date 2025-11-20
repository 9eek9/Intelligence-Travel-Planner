import requests

def get_amadeus_token(api_key, api_secret):
    """
    Generate access token from Amadeus API
    """
    token_url = "https://api.amadeus.com/v1/security/oauth2/token"
    
    data = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": api_secret
    }
    
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    return token_data["access_token"]

def get_flight_offers(origin, destination, depart_date, return_date, api_key, api_secret, target_currency="CAD"):
    # Get access token
    access_token = get_amadeus_token(api_key, api_secret)

    url = "https://api.amadeus.com/v2/shopping/flight-offers"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "currencyCode": target_currency,  # Use dynamic target currency
        "originDestinations": [
            {"id": "1", "originLocationCode": origin, "destinationLocationCode": destination, "departureDateTimeRange": {"date": depart_date}},
            {"id": "2", "originLocationCode": destination, "destinationLocationCode": origin, "departureDateTimeRange": {"date": return_date}}
        ],
        "travelers": [{"id": "1", "travelerType": "ADULT"}],
        "sources": ["GDS"],
        "max": 2
    }
    resp = requests.post(url, json=payload, headers=headers)
    return resp.json()