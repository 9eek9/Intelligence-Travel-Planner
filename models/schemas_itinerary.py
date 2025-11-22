from pydantic import BaseModel
from typing import Optional

class ItineraryCreate(BaseModel):
    user_id: str
    trip_data: dict   