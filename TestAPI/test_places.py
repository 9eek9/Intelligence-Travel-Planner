import os
import googlemaps
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
api_key = os.getenv("GOOGLE_PLACES_API_KEY")

if not api_key:
    raise ValueError(" GOOGLE_PLACES_API_KEY not found in .env file")

# Initialize client
gmaps = googlemaps.Client(key=api_key)

# Example: search for restaurants near Toronto downtown (lat, lng)
places = gmaps.places_nearby(
    location=(43.6532, -79.3832),   # Toronto coordinates
    radius=1000,                    # search radius in meters
    type="tourist_attraction"               # can be 'restaurant' , 'hotel', 'museum', 'tourist_attraction' , etc.
)

# Print results
print(" Found places:")
for place in places.get("results", []):
    print("-", place["name"], "|", place.get("vicinity"))
