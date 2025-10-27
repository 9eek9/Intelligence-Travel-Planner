from fastapi import APIRouter, HTTPException
from models.schemas import ItineraryRequest, ItineraryResponse
from services.places_service import fetch_pois_for_destination
from services.gemini_service import generate_itinerary_text, BUDGET_DESC
from services.sentiment_service import get_sentiment_insights  # sentiment

router = APIRouter()

BUDGET_LABELS = {
    0: "Free",
    1: "Inexpensive",
    2: "Moderate",
    3: "Expensive",
    4: "Luxury"
}

@router.post("/generate", response_model=ItineraryResponse)
def generate(req: ItineraryRequest):
    try:
        pois = fetch_pois_for_destination(
            destination=req.destination,
            max_results_per_type=20,
            kid_friendly=req.kid_friendly,
            budget=req.budget,
            travel_type=req.travel_type,
            activity_theme=req.activity_theme
        )

        attractions = sorted(
            pois["attractions"], key=lambda x: (x.get("rating", 0), x.get("user_ratings_total", 0)), reverse=True
        )
        restaurants = sorted(
            pois["restaurants"], key=lambda x: (x.get("rating", 0), x.get("user_ratings_total", 0)), reverse=True
        )

        per_day = 4
        itinerary_struct = []
        for d in range(req.days):
            day_atts = attractions[d*per_day:(d+1)*per_day]
            day_rests = restaurants[d*2:(d+1)*2]

            # Add sentiment analysis for each place (BEGIN)
            for place in day_atts + day_rests:
                pid = place.get("place_id")
                if pid:
                    try:
                        place["sentiment"] = get_sentiment_insights(pid, place_name=place.get("name"))
                    except Exception:
                        place["sentiment"] = {"summary": "Sentiment unavailable."}
            # Add sentiment analysis for each place (END)

            itinerary_struct.append({"day": d+1, "attractions": day_atts, "restaurants": day_rests})

        text = generate_itinerary_text(
            destination=req.destination,
            days=req.days,
            budget=req.budget,
            kid_friendly=req.kid_friendly,
            plan_struct=itinerary_struct,
            travel_type=req.travel_type,
            activity_theme=req.activity_theme
        )

        return {
            "destination": req.destination,
            "days": req.days,
            "budget": req.budget,
            "budget_label": BUDGET_LABELS.get(req.budget, "Unknown"),
            "budget_description": BUDGET_DESC.get(req.budget, "Moderately priced options"),
            "kid_friendly": req.kid_friendly,
            "itinerary_text": text,
            "plan_struct": itinerary_struct
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
