from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from models.schemas import ItineraryRequest, ItineraryResponse
from services.places_service import fetch_pois_for_destination
from services.gemini_service import generate_itinerary_text, BUDGET_DESC
from database.database import get_db
from models.itinerary import Itinerary
from models.user import User   # NEW

router = APIRouter()

BUDGET_LABELS = {
    0: "Free",
    1: "Inexpensive",
    2: "Moderate",
    3: "Expensive",
    4: "Luxury",
}


@router.post("/generate", response_model=ItineraryResponse)
def generate(req: ItineraryRequest, db: Session = Depends(get_db)):
    """
    Generate itinerary using Google Places + Gemini,
    and save the result into the database, attached to a user.
    """

    try:
        # --------------------------------------------------------
        # 1. Validate user exists ONLY if user_id is provided
        # --------------------------------------------------------
        if req.user_id:
            user = db.query(User).filter(User.id == req.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            user = None   # Guest mode

        # --------------------------------------------------------
        # 2. Fetch POIs (Places of Interest)
        # --------------------------------------------------------
        pois = fetch_pois_for_destination(
            destination=req.destination,
            max_results_per_type=20,
            budget=req.budget,
            travel_type=req.travel_type,
            activity_theme=req.activity_theme,
        )

        # --------------------------------------------------------
        # 3. Sort POIs by rating and popularity
        # --------------------------------------------------------
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

        # --------------------------------------------------------
        # 4. Build itinerary structure per day
        # --------------------------------------------------------
        per_day = 4
        itinerary_struct = []

        for d in range(req.days):
            day_atts = attractions[d * per_day : (d + 1) * per_day]
            day_rests = restaurants[d * 2 : (d + 1) * 2]

            # Remove any previous sentiment field (if exists)
            for place in day_atts + day_rests:
                place.pop("sentiment", None)

            itinerary_struct.append(
                {
                    "day": d + 1,
                    "attractions": day_atts,
                    "restaurants": day_rests,
                }
            )

        # --------------------------------------------------------
        # 5. Generate natural language itinerary using Gemini
        # --------------------------------------------------------
        text = generate_itinerary_text(
            destination=req.destination,
            days=req.days,
            budget=req.budget,
            plan_struct=itinerary_struct,
            travel_type=req.travel_type,
            activity_theme=req.activity_theme,
        )

        # --------------------------------------------------------
        # 6. SAVE to database — now with user_id
        # --------------------------------------------------------
        itinerary_row = Itinerary(
            user_id=req.user_id,              # UPDATED ✔
            destination=req.destination,
            days=req.days,
            budget=req.budget,
            travel_type=req.travel_type,
            activity_theme=req.activity_theme,
            itinerary_text=text,
            plan_struct=itinerary_struct,
        )

        db.add(itinerary_row)
        db.commit()
        db.refresh(itinerary_row)

        # --------------------------------------------------------
        # 7. Return response (same shape as before)
        # --------------------------------------------------------
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

@router.get("/user/{user_id}")
def get_user_itineraries(user_id: str, db: Session = Depends(get_db)):
    """
    Fetch all itineraries belonging to a specific user.
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    itineraries = (
        db.query(Itinerary)
        .filter(Itinerary.user_id == user_id)
        .order_by(Itinerary.created_at.desc())
        .all()
    )

    return {
        "user_id": user_id,
        "count": len(itineraries),
        "itineraries": [
            {
                "id": str(i.id),
                "destination": i.destination,
                "days": i.days,
                "budget": i.budget,
                "travel_type": i.travel_type,
                "activity_theme": i.activity_theme,
                "created_at": i.created_at,
            }
            for i in itineraries
        ],
    }

@router.get("/{itinerary_id}")
def get_itinerary_by_id(itinerary_id: str, db: Session = Depends(get_db)):
    """
    Fetch a single itinerary by its ID.
    """
    itinerary = db.query(Itinerary).filter(Itinerary.id == itinerary_id).first()

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    return {
        "id": str(itinerary.id),
        "user_id": str(itinerary.user_id),
        "destination": itinerary.destination,
        "days": itinerary.days,
        "budget": itinerary.budget,
        "travel_type": itinerary.travel_type,
        "activity_theme": itinerary.activity_theme,
        "itinerary_text": itinerary.itinerary_text,
        "plan_struct": itinerary.plan_struct,
        "created_at": itinerary.created_at,
    }
