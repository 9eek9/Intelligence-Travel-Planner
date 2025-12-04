from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from database.database import Base


# ---------------------------------------------------------
# Summary Cache Table (1 row per place)
# ---------------------------------------------------------
class SentimentCache(Base):
    __tablename__ = "sentiment_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    place_id = Column(String, unique=True, nullable=False)
    place_name = Column(String, nullable=True)

    avg_score = Column(Float, nullable=False)
    positive_ratio = Column(Float, nullable=False)  # 0–100
    keywords = Column(JSONB, nullable=False)        # list
    summary = Column(String, nullable=False)        # numeric summary
    human_summary = Column(String, nullable=False)  # Gemini summary

    num_reviews = Column(Integer, nullable=False)

    photo_url = Column(String, nullable=True)  

    last_updated = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------
# Detailed Raw Review Table (Many rows per place)
# ---------------------------------------------------------
class SentimentReview(Base):
    __tablename__ = "sentiment_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    place_id = Column(String, nullable=False, index=True)

    text = Column(String, nullable=False)
    label = Column(String, nullable=False)          # POSITIVE / NEGATIVE
    score = Column(Float, nullable=False)

    batch_id = Column(UUID(as_uuid=True), nullable=True)
