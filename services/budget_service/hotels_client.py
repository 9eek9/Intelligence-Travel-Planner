import requests
import os
from typing import Dict, Any

def get_hotel_offers(
    city_code: str,
    check_in_date: str,
    check_out_date: str,
    amadeus_key: str,
    amadeus_secret: str,
    currency: str = "USD",
    adults: int = 1,
    max_hotels: int = 5
) -> Dict[str, Any]:
    """
    Get hotel offers using Amadeus API
    
    Step 1: Search hotels by city
    Step 2: Get offers for those hotels
    """
    
    # Get access token
    token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
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
        raise Exception(f"Failed to get access token: {e}")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 1: Search for hotels by city
    print(f"🔍 Searching hotels in {city_code}...")
    search_url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
    search_params = {
        "cityCode": city_code,
        "radius": 50,
        "radiusUnit": "KM",
        "hotelSource": "ALL"
    }
    
    try:
        search_response = requests.get(search_url, headers=headers, params=search_params, timeout=10)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        hotels_list = search_data.get("data", [])
        print(f"   Found {len(hotels_list)} hotels in search")
        
        if not hotels_list:
            print(f"   ⚠️  No hotels found in {city_code}")
            return {"data": []}
        
        # Get first N hotel IDs
        hotel_ids = [h["hotelId"] for h in hotels_list[:max_hotels]]
        print(f"   Selected {len(hotel_ids)} hotels: {hotel_ids}")
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"Failed to search hotels: {e}"
        if e.response is not None:
            error_msg += f" - Response: {e.response.text}"
        raise Exception(error_msg)
    except Exception as e:
        raise Exception(f"Failed to search hotels: {e}")
    
    # Step 2: Get offers for those hotels
    print(f"🏨 Fetching offers for {len(hotel_ids)} hotels...")
    offers_url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
    offers_params = {
        "hotelIds": ",".join(hotel_ids),
        "checkInDate": check_in_date,
        "checkOutDate": check_out_date,
        "adults": adults,
        "currency": currency,
        "bestRateOnly": "true"  # Add this to get only best rates
    }
    
    try:
        offers_response = requests.get(offers_url, headers=headers, params=offers_params, timeout=30)
        
        # Check if we got an error
        if offers_response.status_code == 400:
            error_detail = offers_response.json()
            print(f"   ⚠️  Hotel offers API error: {error_detail}")
            
            # Check if error is due to invalid hotel IDs
            if "errors" in error_detail:
                errors = error_detail["errors"]
                print(f"   Errors: {errors}")
                
                # Try again with fewer hotels or different approach
                if len(hotel_ids) > 3:
                    print(f"   Retrying with fewer hotels...")
                    hotel_ids = hotel_ids[:3]
                    offers_params["hotelIds"] = ",".join(hotel_ids)
                    offers_response = requests.get(offers_url, headers=headers, params=offers_params, timeout=30)
                    
                    if offers_response.status_code != 200:
                        # Still failing - return empty
                        print(f"   ⚠️  Still failing after retry, returning empty results")
                        return {"data": []}
        
        offers_response.raise_for_status()
        offers_data = offers_response.json()
        
        hotel_offers = offers_data.get("data", [])
        print(f"   ✅ Got {len(hotel_offers)} hotel offers")
        
        return offers_data
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"Failed to fetch hotel offers: {e}"
        if e.response is not None:
            try:
                error_json = e.response.json()
                error_msg += f" - Details: {error_json}"
            except:
                error_msg += f" - Response: {e.response.text}"
        
        # Don't raise error, return empty instead
        print(f"   ⚠️  {error_msg}")
        print(f"   Returning empty hotel list")
        return {"data": []}
        
    except Exception as e:
        print(f"   ⚠️  Failed to fetch hotel offers: {e}")
        return {"data": []}


if __name__ == "__main__":
    # Test the client
    from dotenv import load_dotenv
    load_dotenv()
    
    amadeus_key = os.getenv("AMADEUS_API_KEY")
    amadeus_secret = os.getenv("AMADEUS_API_SECRET")
    
    print("Testing hotel search for LAS (Las Vegas)...")
    result = get_hotel_offers(
        city_code="LAS",
        check_in_date="2025-12-01",
        check_out_date="2025-12-05",
        amadeus_key=amadeus_key,
        amadeus_secret=amadeus_secret,
        currency="CAD"
    )
    
    print(f"\n✅ Result: {len(result.get('data', []))} hotels found")
    
    for hotel in result.get("data", [])[:3]:
        hotel_name = hotel.get("hotel", {}).get("name", "Unknown")
        if "offers" in hotel and len(hotel["offers"]) > 0:
            price = hotel["offers"][0]["price"]["total"]
            currency = hotel["offers"][0]["price"]["currency"]
            print(f"   - {hotel_name}: ${price} {currency}")

