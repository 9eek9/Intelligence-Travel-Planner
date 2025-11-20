import os, urllib.parse, requests, time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# Google Places API endpoints
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PHOTO_BASE_URL = "https://maps.googleapis.com/maps/api/place/photo"


def _text_search(query: str):
    """Perform a Google Places Text Search query."""
    params = {"query": query, "key": PLACES_KEY}
    resp = requests.get(TEXT_SEARCH_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


def _get_place_photos(place_id: str, max_photos: int = 5):
    """
    Fetch multiple photo URLs for a place using the Place Details API.
    Returns a list of URLs (can be empty if no photos exist).
    """
    try:
        params = {
            "place_id": place_id,
            "fields": "photos",
            "key": PLACES_KEY
        }
        resp = requests.get(DETAILS_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        photos = data.get("result", {}).get("photos", [])
        photo_refs = [p.get("photo_reference") for p in photos[:max_photos] if p.get("photo_reference")]

        photo_urls = [
            f"{PHOTO_BASE_URL}?maxwidth=800&photo_reference={ref}&key={PLACES_KEY}"
            for ref in photo_refs
        ]
        return photo_urls
    except Exception:
        return []


# def _normalize(results, enrich_photos: bool = False):
#     """Normalize raw Places API results without fetching photos."""
#     out = []
#     for r in results:
#         out.append({
#             "place_id": r.get("place_id"),
#             "name": r.get("name"),
#             "address": r.get("formatted_address"),
#             "lat": r.get("geometry", {}).get("location", {}).get("lat"),
#             "lon": r.get("geometry", {}).get("location", {}).get("lng"),
#             "rating": r.get("rating"),
#             "user_ratings_total": r.get("user_ratings_total"),
#             "price_level": r.get("price_level"),
#             "types": r.get("types", []),
#             # Removed photo_urls completely
#         })
#     return out

# def _normalize(results, enrich_photos: bool = False):
#     out = []
#     for r in results:

#         # Extract ONE photo from Text Search
#         photo_url = None
#         photos = r.get("photos", [])
#         if photos:
#             ref = photos[0].get("photo_reference")
#             if ref:
#                 photo_url = (
#                     f"{PHOTO_BASE_URL}?maxwidth=800&photo_reference={ref}&key={PLACES_KEY}"
#                 )

#         out.append({
#             "place_id": r.get("place_id"),
#             "name": r.get("name"),
#             "address": r.get("formatted_address"),
#             "lat": r.get("geometry", {}).get("location", {}).get("lat"),
#             "lon": r.get("geometry", {}).get("location", {}).get("lng"),
#             "rating": r.get("rating"),
#             "user_ratings_total": r.get("user_ratings_total"),
#             "price_level": r.get("price_level"),
#             "types": r.get("types", []),
#             "photo_url": photo_url,     # ← include 1 photo directly
#         })
#     return out

def _normalize(results, enrich_photos: bool = False):
    out = []

    for r in results:
        place_id = r.get("place_id")

        # ========= 1) Extract ONE text-search photo =========
        photo_url = None
        photos = r.get("photos", [])
        if photos:
            ref = photos[0].get("photo_reference")
            if ref:
                photo_url = (
                    f"{PHOTO_BASE_URL}?maxwidth=800&photo_reference={ref}&key={PLACES_KEY}"
                )

        # ========= 2) Fetch website via Place Details API =========
        website = None
        try:
            details_params = {
                "place_id": place_id,
                "fields": "website",
                "key": PLACES_KEY,
            }
            details_resp = requests.get(DETAILS_URL, params=details_params, timeout=20)
            details_resp.raise_for_status()
            details_data = details_resp.json()
            website = details_data.get("result", {}).get("website")
        except Exception:
            website = None  # fail safely

        # ========= 3) Build booking_url =========
        if website:
            booking_url = website
        else:
            booking_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

        # ========= 4) Build final POI object =========
        out.append({
            "place_id": place_id,
            "name": r.get("name"),
            "address": r.get("formatted_address"),
            "lat": r.get("geometry", {}).get("location", {}).get("lat"),
            "lon": r.get("geometry", {}).get("location", {}).get("lng"),
            "rating": r.get("rating"),
            "user_ratings_total": r.get("user_ratings_total"),
            "price_level": r.get("price_level"),
            "types": r.get("types", []),

            "photo_url": photo_url,
            "website": website,
            "booking_url": booking_url,
        })

    return out



def fetch_pois_for_destination(destination: str,
                               max_results_per_type: int = 20,
                               budget: int = 4,
                               travel_type: str = None,
                               activity_theme: str = None):
    """
    Fetch POIs (Places of Interest) for a destination.

    Filters:
    - budget (0-4)
    - travel_type (e.g. 'family', 'couple', 'solo', 'friends')
    - activity_theme (e.g. 'nature', 'food', 'culture')

    Note:
    - 'Family-friendly' behavior is now derived from travel_type == "family"
      instead of a separate kid_friendly flag.
    """

    # --- Build dynamic query for attractions ---
    query_parts = [f"top tourist attractions in {destination}"]

    # Add activity theme
    if activity_theme:
        query_parts.append(activity_theme)

    # Add travel type flavouring
    if travel_type:
        if travel_type == "couple":
            query_parts.append("romantic places")
        elif travel_type == "family":
            query_parts.append("family friendly")
        elif travel_type == "friends":
            query_parts.append("fun group activities")
        elif travel_type == "solo":
            query_parts.append("solo traveler spots")

    att_query = " ".join(query_parts)
    rest_query = f"best restaurants in {destination}"

    # --- Fetch from Google Places API ---
    attractions_raw = _text_search(att_query)
    restaurants_raw = _text_search(rest_query)

    # --- Normalize and enrich photo data ---
    atts = _normalize(attractions_raw[:max_results_per_type], enrich_photos=False)
    rests = _normalize(restaurants_raw[:max_results_per_type], enrich_photos=False)

    # --- Budget filter (0–4) ---
    atts = [
        a for a in atts
        if (a.get("price_level") is not None and a["price_level"] <= budget)
        or a.get("price_level") is None
    ]
    rests = [
        r for r in rests
        if (r.get("price_level") is not None and r["price_level"] <= budget)
        or r.get("price_level") is None
    ]

    # --- Rating threshold ---
    atts = [a for a in atts if a.get("rating", 0) >= 3.5]
    rests = [r for r in rests if r.get("rating", 0) >= 3.5]

    # --- Extra logic for family trips (soft filter, not too strict) ---
    if travel_type == "family":
        family_types = [
            "park", "zoo", "aquarium", "museum",
            "amusement_park", "tourist_attraction", "playground"
        ]

        def is_family_friendly(place):
            types_str = ",".join(place.get("types", []))
            return any(t in types_str for t in family_types)

        family_atts = [a for a in atts if is_family_friendly(a)]
        # If we found some family-friendly ones, prefer them;
        # otherwise fall back to original list so the user still gets results.
        if family_atts:
            atts = family_atts

    return {"attractions": atts, "restaurants": rests}

