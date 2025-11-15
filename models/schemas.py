from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

# Request body model
class ItineraryRequest(BaseModel):
    destination: str
    days: int
    budget: int  # 0–4
    travel_type: Optional[Literal["solo", "couple", "family", "friends"]] = None
    activity_theme: Optional[str] = None

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
    destination: str
    days: int
    budget: int
    budget_label: str
    budget_description: str
    itinerary_text: str
    plan_struct: List[Any]

# === Chatbot + Language Buddy (BEGIN) === #
class ChatbotRequest(BaseModel):
    message: str = Field(..., description="User message for travel Q&A")

class ChatbotResponse(BaseModel):
    reply: str

LanguageMode = Literal["translate", "correct", "explain"]

class LanguageBuddyRequest(BaseModel):
    message: str
    mode: LanguageMode = "translate"
    source_lang: Optional[str] = None   # e.g., "my", "en", "ja"
    target_lang: str = "en"
    tone: str = "polite"                # "polite" | "casual"

class LanguageBuddyResponse(BaseModel):
    reply: str
# === Chatbot + Language Buddy (END) === #