# services/sentiment_service.py
import os
import requests
import numpy as np
from dotenv import load_dotenv
from transformers import pipeline
from sklearn.feature_extraction.text import CountVectorizer
import google.generativeai as genai

from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.sentiment_review import SentimentCache

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
genai.configure(api_key=GEMINI_KEY)

PLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


# ---------------------------------------------------------
# Fetch place name using Google Place Details API
# ---------------------------------------------------------
def get_place_name(place_id: str):
    """Fetch only the place name from Google Places."""
    try:
        params = {
            "place_id": place_id,
            "fields": "name",
            "key": PLACES_KEY,
        }
        resp = requests.get(DETAILS_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", {}).get("name")
    except Exception:
        return None


# ---------------------------------------------------------
# Fetch basic place details (for /sentiment/{place_id})
# ---------------------------------------------------------
def get_place_basic_details(place_id: str):
    """
    Fetch basic details for a place: name, address, rating, user_ratings_total, photo_url.

    Used mainly by /sentiment/{place_id} to build a rich 'place' block.
    """
    try:
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,rating,user_ratings_total,photos",
            "key": PLACES_KEY,
        }
        resp = requests.get(DETAILS_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json().get("result", {}) or {}

        name = data.get("name")
        address = data.get("formatted_address")
        rating = data.get("rating")
        user_ratings_total = data.get("user_ratings_total")

        # Derive a photo URL, if photos are present
        photo_url = None
        photos = data.get("photos", [])
        if photos:
            photo_ref = photos[0].get("photo_reference")
            if photo_ref:
                photo_url = (
                    f"https://maps.googleapis.com/maps/api/place/photo"
                    f"?maxwidth=800"
                    f"&photo_reference={photo_ref}"
                    f"&key={PLACES_KEY}"
                )

        return {
            "name": name,
            "address": address,
            "rating": rating,
            "user_ratings_total": user_ratings_total,
            "photo_url": photo_url,
        }

    except Exception:
        return {
            "name": None,
            "address": None,
            "rating": None,
            "user_ratings_total": None,
            "photo_url": None,
        }


# ---------------------------------------------------------
# Fetch reviews from Google Places
# ---------------------------------------------------------
def get_place_reviews(place_id: str, max_reviews: int = 5):
    """Fetch up to 5 latest reviews for a given Google place."""
    try:
        params = {
            "place_id": place_id,
            "fields": "reviews",
            "key": PLACES_KEY,
        }
        resp = requests.get(DETAILS_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        reviews = data.get("result", {}).get("reviews", [])
        return [r.get("text", "") for r in reviews if r.get("text")][:max_reviews]
    except Exception:
        return []


def get_place_photo_url(place_id: str, max_width: int = 800):
    """
    Fetch the first photo reference for a place and convert it
    into a real Google Place Photo URL.
    """
    try:
        params = {
            "place_id": place_id,
            "fields": "photos",
            "key": PLACES_KEY,
        }
        resp = requests.get(DETAILS_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        photos = data.get("result", {}).get("photos", [])
        if not photos:
            return None

        # Use the FIRST photo reference
        photo_ref = photos[0].get("photo_reference")
        if not photo_ref:
            return None

        # Generate actual accessible URL
        url = (
            f"https://maps.googleapis.com/maps/api/place/photo"
            f"?maxwidth={max_width}"
            f"&photo_reference={photo_ref}"
            f"&key={PLACES_KEY}"
        )

        return url

    except Exception:
        return None


# ---------------------------------------------------------
# Run DistilBERT sentiment analysis
# ---------------------------------------------------------
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english",
)


def analyze_reviews(reviews):
    """Analyze sentiment (POSITIVE / NEGATIVE + score)."""
    results = []
    for text in reviews:
        try:
            out = sentiment_pipeline(text[:512])[0]  # truncate long reviews
            results.append(
                {
                    "text": text,
                    "label": out["label"],
                    "score": float(round(out["score"], 3)),  # ensure Python float
                }
            )
        except Exception:
            continue
    return results


# ---------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------
def extract_keywords(texts, max_keywords=5):
    if not texts:
        return []

    try:
        vectorizer = CountVectorizer(stop_words="english", max_features=50)
        X = vectorizer.fit_transform(texts)
        counts = X.toarray().sum(axis=0)
        vocab = vectorizer.get_feature_names_out()

        top_indices = counts.argsort()[::-1][:max_keywords]
        return [str(vocab[i]) for i in top_indices]
    except Exception:
        return []


# ---------------------------------------------------------
# Summarize sentiment numbers
# ---------------------------------------------------------
def summarize_sentiment(results):
    """Aggregate numeric sentiment statistics."""
    if not results:
        return {
            "avg_score": 0.0,
            "positive_ratio": 0.0,
            "keywords": [],
            "summary": "No reviews available.",
        }

    pos = [r["score"] for r in results if r["label"] == "POSITIVE"]
    neg = [r["score"] for r in results if r["label"] == "NEGATIVE"]

    avg_score = np.mean(pos + [-s for s in neg]) if results else 0.0
    positive_ratio = len(pos) / len(results) if results else 0.0

    summary = (
        f"{positive_ratio * 100:.1f}% of reviews are positive "
        f"with an average score of {avg_score:+.2f}."
    )

    return {
        "avg_score": float(round(avg_score, 2)),
        "positive_ratio": float(round(positive_ratio * 100, 1)),
        "keywords": extract_keywords([r["text"] for r in results]),
        "summary": summary,
    }


# ---------------------------------------------------------
# Gemini LLM summary
# ---------------------------------------------------------
def summarize_with_gemini(place_name: str, sentiment_data: dict, reviews: list):
    """Generate human-style description of sentiment."""
    try:
        model = genai.GenerativeModel(MODEL_NAME)

        reviews_text = "\n".join([r["text"] for r in reviews[:5]]) or "No reviews found."

        prompt = f"""
You are an AI travel assistant. Based on the following Google reviews for {place_name},
write ONE short, human-like summary (max 2 sentences).

Sentiment Statistics:
- {sentiment_data["summary"]}
- Positive ratio: {sentiment_data["positive_ratio"]}%
- Keywords: {', '.join(sentiment_data['keywords'])}

Reviews:
{reviews_text}

Example format:
"Most travelers enjoyed the skyline views but mentioned long wait times."

Now write your summary:
"""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception:
        return "Visitors had mixed experiences."


# ---------------------------------------------------------
# Main: Sentiment Insights with DB Cache
# ---------------------------------------------------------
def get_sentiment_insights(place_id: str, place_name: str | None = None):
    """
    Return sentiment for a place:
      1) Check DB cache
      2) If not found, compute → save → return

    Also returns a photo_url (either from cache or a fresh lookup),
    and we include it in the sentiment payload for consistency.
    """
    db: Session = SessionLocal()

    try:
        # -------------------------
        # 1) Try cached result
        # -------------------------
        cached = db.query(SentimentCache).filter_by(place_id=place_id).first()

        if cached:
            return {
                "place_id": cached.place_id,
                "place_name": cached.place_name,
                "num_reviews": int(cached.num_reviews),
                "summary": cached.summary,
                "avg_score": float(cached.avg_score),
                "positive_ratio": float(cached.positive_ratio),
                "keywords": cached.keywords,
                "human_summary": cached.human_summary,
                "photo_url": cached.photo_url,  
                "last_updated": (
                    cached.last_updated.isoformat()
                    if cached.last_updated
                    else None
                ),
            }

        # -------------------------
        # 2) Not cached → process reviews
        # -------------------------
        # Fetch place name if missing (ID endpoint)
        if not place_name:
            place_name = get_place_name(place_id)

        reviews = get_place_reviews(place_id)
        analyzed = analyze_reviews(reviews)
        summary = summarize_sentiment(analyzed)

        gemini_summary = summarize_with_gemini(
            place_name or "this place", summary, analyzed
        )

        # Get photo URL for this place
        photo_url = get_place_photo_url(place_id)

        # -------------------------
        # 3) Save to DB
        # -------------------------
        cache_row = SentimentCache(
            place_id=place_id,
            place_name=place_name or get_place_name(place_id),
            avg_score=float(summary["avg_score"]),
            positive_ratio=float(summary["positive_ratio"]),
            keywords=summary["keywords"],  # JSON-safe
            summary=summary["summary"],
            human_summary=gemini_summary,
            num_reviews=int(len(reviews)),
            photo_url=photo_url, 
        )

        db.add(cache_row)
        db.commit()

        # -------------------------
        # 4) Final return
        # -------------------------
        return {
            "place_id": place_id,
            "place_name": place_name,
            "num_reviews": len(reviews),
            "summary": summary["summary"],
            "avg_score": summary["avg_score"],
            "positive_ratio": summary["positive_ratio"],
            "keywords": summary["keywords"],
            "human_summary": gemini_summary,
            "photo_url": photo_url,     
            "samples": analyzed[:3],
        }

    finally:
        db.close()
