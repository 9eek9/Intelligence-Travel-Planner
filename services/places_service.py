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


def _normalize(results, enrich_photos: bool = True):
    """Normalize raw Places API results with optional multi-photo enrichment."""
    out = []
    for r in results:
        # Default: use any photo provided by text search
        photo_urls = []
        photos = r.get("photos", [])
        if photos:
            ref = photos[0].get("photo_reference")
            if ref:
                photo_urls.append(
                    f"{PHOTO_BASE_URL}?maxwidth=800&photo_reference={ref}&key={PLACES_KEY}"
                )

        # Optionally fetch more photos using Place Details
        if enrich_photos and r.get("place_id"):
            extra_photos = _get_place_photos(r["place_id"], max_photos=5)
            # Avoid duplicates
            for url in extra_photos:
                if url not in photo_urls:
                    photo_urls.append(url)
            # Small delay to avoid hitting quota too quickly
            time.sleep(0.2)

        out.append({
            "name": r.get("name"),
            "address": r.get("formatted_address"),
            "lat": r.get("geometry", {}).get("location", {}).get("lat"),
            "lon": r.get("geometry", {}).get("location", {}).get("lng"),
            "rating": r.get("rating"),
            "user_ratings_total": r.get("user_ratings_total"),
            "price_level": r.get("price_level"),
            "types": r.get("types", []),
            "photo_urls": photo_urls
        })
    return out


def fetch_pois_for_destination(destination: str,
                               max_results_per_type: int = 20,
                               kid_friendly: bool = False,
                               budget: int = 4,
                               travel_type: str = None,
                               activity_theme: str = None):
    """
    Fetch POIs (Places of Interest) for a destination.
    Includes filters (kid_friendly, budget, travel_type, activity_theme)
    and multiple photo URLs per place (via Place Details API).
    """

    # --- Build dynamic query for attractions ---
    query_parts = [f"top tourist attractions in {destination}"]

    # Add activity theme
    if activity_theme:
        query_parts.append(activity_theme)

    # Add travel type
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
    atts = _normalize(attractions_raw[:max_results_per_type], enrich_photos=True)
    rests = _normalize(restaurants_raw[:max_results_per_type], enrich_photos=True)

    # --- Kid-friendly filter ---
    if kid_friendly:
        atts = [
            a for a in atts
            if "park" in ",".join(a["types"]) or "museum" in ",".join(a["types"])
        ]

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

    return {"attractions": atts, "restaurants": rests}
