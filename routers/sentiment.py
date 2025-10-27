from fastapi import APIRouter, HTTPException, Query
from services.places_service import _text_search, _normalize
from services.sentiment_service import get_sentiment_insights, get_place_reviews

router = APIRouter()


@router.get("/analyze")
def sentiment_by_name(query: str = Query(..., description="Place name or location to analyze")):
    """
    Analyze sentiment for a given place name using Google Places search.
    Example: /sentiment/analyze?query=CN Tower Toronto
    """
    try:
        search_results = _text_search(query)
        if not search_results:
            raise HTTPException(status_code=404, detail=f"No places found for '{query}'.")

        places = _normalize(search_results, enrich_photos=False)

        # Try each place until one has reviews
        for place in places[:5]:
            pid = place.get("place_id")
            if not pid:
                continue

            reviews = get_place_reviews(pid)
            if reviews:
                sentiment = get_sentiment_insights(pid, place_name=place.get("name"))
                return {
                    "place": {
                        "name": place.get("name"),
                        "address": place.get("address"),
                        "rating": place.get("rating"),
                        "user_ratings_total": place.get("user_ratings_total"),
                        "place_id": pid
                    },
                    "sentiment": sentiment
                }

        # None had reviews
        return {
            "message": f"No public reviews found for '{query}'.",
            "suggestion": "Try a more specific place name (e.g., 'Space Needle Seattle').",
            "possible_matches": [
                {
                    "name": p.get("name"),
                    "address": p.get("address"),
                    "place_id": p.get("place_id"),
                    "rating": p.get("rating")
                }
                for p in places[:5]
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{place_id}")
def sentiment_by_id(place_id: str):
    """Get sentiment summary for a specific Google Place ID."""
    try:
        return get_sentiment_insights(place_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
