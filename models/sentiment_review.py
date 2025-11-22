from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from database.database import Base


class SentimentCache(Base):
    __tablename__ = "sentiment_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    place_id = Column(String, unique=True, nullable=False)
    place_name = Column(String, nullable=True)

    avg_score = Column(Float, nullable=False)
    positive_ratio = Column(Float, nullable=False)  # 0–100
    keywords = Column(JSONB, nullable=False)        # list
    summary = Column(String, nullable=False)        # numeric review summary
    human_summary = Column(String, nullable=False)  # Gemini text summary

    num_reviews = Column(Integer, nullable=False)

    photo_url = Column(String, nullable=True) # photo URL for this place

    last_updated = Column(DateTime, default=datetime.utcnow)
