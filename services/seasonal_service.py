import os
import requests
import random
from datetime import datetime
import httpx   # IMPORTANT: async HTTP client

from config import (
    CALENDARIFIC_API_KEY,
    PREDICTHQ_TOKEN,
    OPENTRIP_API_KEY,
    UNSPLASH_KEY
)

# ML scoring
from services.ml_utils import (
    predict_attraction_popularity,
    predict_event_popularity
)

# ======================================================
# 1. DESTINATION RESOLUTION
# ======================================================

def get_coordinates(place_name: str):
    """Resolve coordinates using Nominatim."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": place_name, "format": "json", "limit": 1},
            headers={"User-Agent": "SmartTravelApp/1.0"}
        )
        data = r.json()
        if not data:
            return None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print("❌ get_coordinates:", e)
        return None


def resolve_country_code(place_name: str):
    """Get ISO country code."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": place_name, "format": "json", "limit": 1, "addressdetails": 1},
            headers={"User-Agent": "SmartTravelApp/1.0"}
        )
        data = r.json()
        if not data:
            return None
        return data[0]["address"].get("country_code", "").upper()
    except Exception:
        return None


def determine_best_season(lat: float):
    """Simple seasonal logic."""
    if lat > 23 or lat < -23:
        return "Summer"
    return "All Year"

# ======================================================
# 2. UNSPLASH IMAGE FETCHING (SAFE)
# ======================================================

def get_unsplash_image(query: str):
    """
    Fetch a SINGLE relevant Unsplash image safely.
    Handles 403 rate limits gracefully.
    """
    if not UNSPLASH_KEY:
        return f"https://source.unsplash.com/1600x900/?{query}"

    try:
        url = "https://api.unsplash.com/search/photos"
        r = requests.get(url, params={
            "query": query,
            "orientation": "landscape",
            "per_page": 1,
            "client_id": UNSPLASH_KEY
        })

        if r.status_code == 403:
            print("⚠ Unsplash rate limit — using fallback.")
            return f"https://source.unsplash.com/1600x900/?{query}"

        data = r.json()
        if data.get("results"):
            return data["results"][0]["urls"]["regular"]

    except Exception as e:
        print("❌ Unsplash error:", e)

    return f"https://source.unsplash.com/1600x900/?{query}"

# ======================================================
# 3. OPENTRIPMAP ATTRACTIONS (ASYNC)
# ======================================================

import httpx

async def fetch_otm_attractions(destination: str, radius: int = 4000, limit: int = 12):
    """
    Fetch attractions using OpenTripMap:
    - geoname lookup → lat/lon
    - radius search
    - detail fetch (for preview image + description)
    """

    # STEP 1 — Get city coordinates from OpenTripMap
    geoname_url = (
        f"https://api.opentripmap.com/0.1/en/places/geoname?"
        f"name={destination}&apikey={OPENTRIP_API_KEY}"
    )

    async with httpx.AsyncClient(timeout=10) as client:
        geo_res = await client.get(geoname_url)

    if geo_res.status_code != 200:
        print("[OTM] Geoname lookup failed:", geo_res.text)
        return []

    geo = geo_res.json()
    if "lat" not in geo:
        print("[OTM] No coordinates found for:", destination)
        return []

    lat, lon = geo["lat"], geo["lon"]

    # STEP 2 — Radius search
    radius_url = (
        f"https://api.opentripmap.com/0.1/en/places/radius?"
        f"radius={radius}&lon={lon}&lat={lat}&limit={limit}&apikey={OPENTRIP_API_KEY}"
    )

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(radius_url)

    if r.status_code != 200:
        print("[OTM] Radius error:", r.text)
        return []

    features = r.json().get("features", [])
    if not features:
        print("[OTM] No attractions found")
        return []

    results = []

    # STEP 3 — Fetch details for each attraction
    async with httpx.AsyncClient(timeout=10) as client:
        for item in features:
            xid = item["properties"].get("xid")
            if not xid:
                continue

            detail_url = f"https://api.opentripmap.com/0.1/en/places/xid/{xid}?apikey={OPENTRIP_API_KEY}"
            detail_res = await client.get(detail_url)

            if detail_res.status_code != 200:
                continue

            detail = detail_res.json()

            name = detail.get("name", "Unknown Place")
            desc = (
                detail.get("wikipedia_extracts", {}).get("text")
                or detail.get("info", {}).get("descr")
                or "A popular attraction in this area."
            )

            image = detail.get("preview", {}).get("source")
            if not image:
                image = f"https://source.unsplash.com/800x600/?{name.replace(' ', '%20')}"

            results.append({
                "name": name,
                "description": desc,
                "image": image,
                "popularity_score": random.randint(70, 95)
            })

    return results


# ======================================================
# 4. HOLIDAYS USING CALENDARIFIC
# ======================================================

def fetch_holidays(country_code, start, end):
    if not CALENDARIFIC_API_KEY:
        return []

    out = []
    year_start = int(start[:4])
    year_end = int(end[:4])

    for y in range(year_start, year_end + 1):
        try:
            r = requests.get(
                "https://calendarific.com/api/v2/holidays",
                params={
                    "api_key": CALENDARIFIC_API_KEY,
                    "country": country_code.lower(),
                    "year": y
                }
            )

            holidays = r.json().get("response", {}).get("holidays", [])

            for h in holidays:
                date = h.get("date", {}).get("iso", "")[:10]
                if start <= date <= end:
                    name = h.get("name", "")
                    out.append({
                        "name": name,
                        "description": h.get("description", ""),
                        "date": date,
                        "type": "holiday",
                        "category": h.get("type", ["holiday"])[0],
                        "image": get_unsplash_image(name),
                        "popularity_score": 0
                    })

        except Exception as e:
            print("❌ fetch_holidays:", e)

    return out

# ======================================================
# 5. EVENTS USING PREDICTHQ
# ======================================================

def fetch_events(country_code, start, end):
    if not PREDICTHQ_TOKEN:
        return []

    try:
        r = requests.get(
            "https://api.predicthq.com/v1/events/",
            headers={"Authorization": f"Bearer {PREDICTHQ_TOKEN}"},
            params={
                "country": country_code.upper(),
                "start.gte": start,
                "start.lte": end,
                "limit": 30
            }
        )

        events = r.json().get("results", [])
        out = []

        for e in events:
            title = e.get("title", "")
            date = e.get("start", "")[:10]

            out.append({
                "name": title,
                "description": e.get("description", ""),
                "date": date,
                "type": "event",
                "category": e.get("category", "event"),
                "image": get_unsplash_image(title),
                "popularity_score": 0
            })

        return out

    except Exception as e:
        print("❌ fetch_events:", e)
        return []

# ======================================================
# 6. MAIN LOGIC (CALLED BY ROUTER)
# ======================================================

async def get_seasonal_suggestions(destination: str, start: str, end: str):

    coords = get_coordinates(destination)
    if not coords:
        return {"status": "error", "message": f"Could not locate '{destination}'"}

    lat, lon = coords
    country = resolve_country_code(destination)
    season = determine_best_season(lat)

    # -----------------------------
    # FIXED: correct async attraction fetching
    # -----------------------------
    attractions = await fetch_otm_attractions(destination)

    holidays = fetch_holidays(country, start, end)
    events = fetch_events(country, start, end)

    # ======================================================
    # ML popularity scoring
    # ======================================================

    for a in attractions:
        a["popularity_score"] = predict_attraction_popularity(a)

    for h in holidays:
        h["popularity_score"] = random.randint(60, 90)

    for e in events:
        ml_score = predict_event_popularity(e)
        rule = random.randint(50, 90)
        e["popularity_score"] = int(ml_score * 0.4 + rule * 0.6)

    return {
        "status": "ok",
        "meta": {
            "destination": destination,
            "start": start,
            "end": end,
            "country": country,
            "best_season": season
        },
        "results": {
            "attractions": attractions,
            "events": holidays + events
        }
    }
