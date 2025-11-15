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
    """
    Generate itinerary using Google Places (with photos) and Gemini LLM.
    """
    try:
        # --- Step 1. Fetch POIs (Places of Interest) ---
        pois = fetch_pois_for_destination(
            destination=req.destination,
            max_results_per_type=20,
            budget=req.budget,
            travel_type=req.travel_type,
            activity_theme=req.activity_theme,
        )

        # --- Step 2. Sort places by rating & popularity ---
        attractions = sorted(
            pois["attractions"],
            key=lambda x: (x.get("rating", 0), x.get("user_ratings_total", 0)),
            reverse=True,
        )
        restaurants = sorted(
            pois["restaurants"],
            key=lambda x: (x.get("rating", 0), x.get("user_ratings_total", 0)),
            reverse=True,
        )

        # --- Step 3. Build itinerary structure ---
        per_day = 4
        itinerary_struct = []
        for d in range(req.days):
            day_atts = attractions[d * per_day : (d + 1) * per_day]
            day_rests = restaurants[d * 2 : (d + 1) * 2]

            # Keep place_id for later sentiment fetch
            for place in day_atts + day_rests:
                place.pop("sentiment", None)  # remove any previous sentiment field

            itinerary_struct.append(
                {
                    "day": d + 1,
                    "attractions": day_atts,
                    "restaurants": day_rests,
                }
            )

        # --- Step 4. Generate natural language itinerary using Gemini ---
        text = generate_itinerary_text(
            destination=req.destination,
            days=req.days,
            budget=req.budget,
            plan_struct=itinerary_struct,
            travel_type=req.travel_type,
            activity_theme=req.activity_theme,
        )

        # --- Step 5. Return structured response ---
        return {
            "destination": req.destination,
            "days": req.days,
            "budget": req.budget,
            "budget_label": BUDGET_LABELS.get(req.budget, "Unknown"),
            "budget_description": BUDGET_DESC.get(
                req.budget, "Moderately priced options"
            ),
            "itinerary_text": text,
            "plan_struct": itinerary_struct,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

