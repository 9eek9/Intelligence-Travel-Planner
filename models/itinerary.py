# models/itinerary.py

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from database.database import Base

class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    destination = Column(String, nullable=False)
    days = Column(Integer, nullable=False)
    budget = Column(Integer, nullable=False)
    travel_type = Column(String, nullable=True)
    activity_theme = Column(String, nullable=True)
    itinerary_text = Column(String, nullable=False)
    plan_struct = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
