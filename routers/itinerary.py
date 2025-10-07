from fastapi import APIRouter, HTTPException
from models.schemas import ItineraryRequest, ItineraryResponse
from services.places_service import fetch_pois_for_destination
from services.gemini_service import generate_itinerary_text, BUDGET_DESC

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
        # Calls get_places(destination) from places_service.py to get attractions & restaurants.
        pois = fetch_pois_for_destination(
            destination=req.destination,
            max_results_per_type=20,
            kid_friendly=req.kid_friendly,
            budget=req.budget
        )

        # Sorts by rating and reviews.
        attractions = sorted(
            pois["attractions"], key=lambda x: (x.get("rating", 0), x.get("user_ratings_total", 0)), reverse=True
        )
        restaurants = sorted(
            pois["restaurants"], key=lambda x: (x.get("rating", 0), x.get("user_ratings_total", 0)), reverse=True
        )
        
        # Slices top results (4 attractions + 2 restaurants per day)
        # Builds a structured plan (a simple JSON)
        per_day = 4
        itinerary_struct = []
        for d in range(req.days):
            day_atts = attractions[d*per_day:(d+1)*per_day]
            day_rests = restaurants[d*2:(d+1)*2]
            itinerary_struct.append({"day": d+1, "attractions": day_atts, "restaurants": day_rests})

        # Sends that JSON to Gemini (generate_itinerary_with_gemini), which writes a narrative summary (“On Day 1, you can start with …”)
        text = generate_itinerary_text(
            destination=req.destination,
            days=req.days,
            budget=req.budget,
            kid_friendly=req.kid_friendly,
            plan_struct=itinerary_struct
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
