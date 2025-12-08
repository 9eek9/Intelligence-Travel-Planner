import requests
from typing import List, Dict
from fx_client import convert_currency


def fetch_activities(start_date: str, end_date: str, amadeus_key: str, amadeus_secret: str, latitude: float, longitude: float, target_currency: str) -> List[Dict]:
    """
    Fetch activities for a given city and date range using the Amadeus API, and convert prices to target currency.
    """
    # Step 1: Get access token
    token_url = "https://api.amadeus.com/v1/security/oauth2/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": amadeus_key,
        "client_secret": amadeus_secret
    }

    try:
        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
    except Exception as e:
        print(f"Failed to get access token: {e}")
        return []

    # Step 2: Fetch activities
    amadeus_api_url = "https://api.amadeus.com/v1/shopping/activities"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "startDate": start_date,
        "endDate": end_date
    }

    try:
        response = requests.get(amadeus_api_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        activities = response.json().get("data", [])

        return activities
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch activities: {e}")
        return []

def get_city_geocode(city_name: str, amadeus_key: str, amadeus_secret: str):
    """
    Fetch latitude, longitude, and city code for a city using Amadeus city search API.
    """
    # Get access token
    token_url = "https://api.amadeus.com/v1/security/oauth2/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": amadeus_key,
        "client_secret": amadeus_secret
    }
    try:
        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
    except Exception as e:
        print(f"Failed to get access token for city geocode: {e}")
        return None, None, None

    # Search city
    search_url = "https://api.amadeus.com/v1/reference-data/locations/cities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "keyword": city_name,
        "max": 1
    }
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("meta", {}).get("count", 0) > 0:
            city_data = data["data"][0]
            geo = city_data["geoCode"]
            city_code = city_data.get("iataCode")  # Extract city code
            return geo["latitude"], geo["longitude"], city_code
        else:
            print(f"No city found for {city_name}")
            return None, None, None
    except Exception as e:
        print(f"Failed to fetch city geocode: {e}")
        return None, None, None

def fetch_activities_by_city_name(city_name: str,  start_date: str, end_date: str, amadeus_key: str, amadeus_secret: str, target_currency: str):
    """
    Fetch activities for a city name by first retrieving its latitude and longitude.
    """
    # Get latitude and longitude using the city name and country code
    latitude, longitude, city_code = get_city_geocode(city_name, amadeus_key, amadeus_secret)
    if latitude is None or longitude is None:
        print(f"Could not get latitude/longitude for {city_name}")
        return []

    # Fetch activities using the latitude and longitude
    return fetch_activities(start_date, end_date, amadeus_key, amadeus_secret, latitude, longitude, target_currency)