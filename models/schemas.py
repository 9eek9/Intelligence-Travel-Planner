from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# Request body model
class ItineraryRequest(BaseModel):
    destination: str = Field(..., example="Toronto")
    days: int = Field(..., example=3)
    budget: int = Field(..., example=2, description="0=Free, 1=Inexpensive, 2=Moderate, 3=Expensive, 4=Luxury")
    kid_friendly: bool = Field(False, example=True)
    travel_type: Optional[str] = Field(None, example="couple", description="solo | couple | family | friends")
    activity_theme: Optional[str] = Field(None, example="adventure", description="relaxing | adventure | cultural | shopping")


# One day of itinerary (nested inside response)
class ItineraryDay(BaseModel):
    day: int = Field(..., example=1)
    attractions: List[Dict[str, Any]] = Field(
        ..., example=[{"name": "CN Tower", "rating": 4.7, "price_level": 3}]
    )
    restaurants: List[Dict[str, Any]] = Field(
        ..., example=[{"name": "Pizzeria Libretto", "rating": 4.5, "price_level": 1}]
    )


# Full response model
class ItineraryResponse(BaseModel):
    destination: str = Field(..., example="Toronto")
    days: int = Field(..., example=3)
    budget: int = Field(..., example=2)
    budget_label: str = Field(..., example="Moderate")
    budget_description: str = Field(
        ..., example="moderately priced options such as mid-range restaurants and affordable activities"
    )
    kid_friendly: bool = Field(..., example=True)
    itinerary_text: str = Field(
        ...,
        example="Day 1: Start your trip at the CN Tower... Day 2: Explore Royal Ontario Museum..."
    )
    plan_struct: List[ItineraryDay] = Field(
        ..., example=[
            {
                "day": 1,
                "attractions": [{"name": "CN Tower", "rating": 4.7}],
                "restaurants": [{"name": "Pizzeria Libretto", "rating": 4.5}]
            },
            {
                "day": 2,
                "attractions": [{"name": "Royal Ontario Museum", "rating": 4.6}],
                "restaurants": [{"name": "Kinka Izakaya", "rating": 4.4}]
            }
        ]
    )
