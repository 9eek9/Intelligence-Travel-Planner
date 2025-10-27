from fastapi import APIRouter, HTTPException, Query
from services.places_service import _text_search
from services.sentiment_service import get_sentiment_insights

router = APIRouter()

@router.get("/{place_id}")
def sentiment_by_id(place_id: str):
    """Get sentiment summary for a specific Google Place ID."""
    try:
        return get_sentiment_insights(place_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze")
def sentiment_by_name(query: str = Query(..., description="Place name or location to analyze")):
    """
    Analyze sentiment for a given place name using Google Places search.
    Example: /sentiment/analyze?query=CN Tower Toronto
    """
    try:
        # Search place from name
        results = _text_search(query)
        print("🔍 Text Search Result:", results[0])
        if not results:
            raise HTTPException(status_code=404, detail="No places found for this name.")
        place = results[0]
        pid = place.get("place_id")
        if not pid:
            raise HTTPException(status_code=400, detail="Place ID not found.")
        # Get sentiment insights
        sentiment = get_sentiment_insights(pid, place_name=place.get("name"))
        return {"place": place, "sentiment": sentiment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
