import os, urllib.parse, requests
from dotenv import load_dotenv

load_dotenv()
PLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

BASE_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

def _text_search(query: str):
    params = {"query": query, "key": PLACES_KEY}
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])

def _normalize(results):
    out = []
    for r in results:
        out.append({
            "name": r.get("name"),
            "address": r.get("formatted_address"),
            "lat": r.get("geometry", {}).get("location", {}).get("lat"),
            "lon": r.get("geometry", {}).get("location", {}).get("lng"),
            "rating": r.get("rating"),
            "user_ratings_total": r.get("user_ratings_total"),
            "price_level": r.get("price_level"),
            "types": r.get("types", [])
        })
    return out

def fetch_pois_for_destination(destination: str, max_results_per_type: int = 20, kid_friendly: bool = False, budget: int = 4):
    att_query = f"top tourist attractions in {destination}"
    rest_query = f"best restaurants in {destination}"

    atts = _normalize(_text_search(att_query))[:max_results_per_type]
    rests = _normalize(_text_search(rest_query))[:max_results_per_type]

    # Kid-friendly filter
    if kid_friendly:
        atts = [
            a for a in atts
            if "park" in ",".join(a["types"]) or "museum" in ",".join(a["types"])
        ]

    # Budget filter (apply to both attractions + restaurants)
    atts = [
        a for a in atts
        if (a.get("price_level") is not None and a["price_level"] <= budget)
        or a.get("price_level") is None   # allow attractions without price info
    ]
    rests = [
        r for r in rests
        if (r.get("price_level") is not None and r["price_level"] <= budget)
        or r.get("price_level") is None   # allow restaurants without price info
    ]

    return {"attractions": atts, "restaurants": rests}

