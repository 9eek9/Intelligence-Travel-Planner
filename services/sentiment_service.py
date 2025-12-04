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
from models.sentiment_review import SentimentCache, SentimentReview

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
genai.configure(api_key=GEMINI_KEY)

PLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


# ---------------------------------------------------------
# GET PLACE NAME (used if missing)
# ---------------------------------------------------------
def get_place_name(place_id: str):
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
    except:
        return None


# ---------------------------------------------------------
# BASIC DETAILS (rating, address, etc.)
# ---------------------------------------------------------
def get_place_basic_details(place_id: str):
    try:
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,rating,user_ratings_total,photos",
            "key": PLACES_KEY,
        }
        resp = requests.get(DETAILS_URL, params=params, timeout=20)
        data = resp.json().get("result", {}) or {}

        name = data.get("name")
        address = data.get("formatted_address")
        rating = data.get("rating")
        user_ratings_total = data.get("user_ratings_total")

        photo_url = None
        photos = data.get("photos", [])
        if photos:
            ref = photos[0].get("photo_reference")
            if ref:
                photo_url = (
                    f"https://maps.googleapis.com/maps/api/place/photo"
                    f"?maxwidth=800&photo_reference={ref}&key={PLACES_KEY}"
                )

        return {
            "name": name,
            "address": address,
            "rating": rating,
            "user_ratings_total": user_ratings_total,
            "photo_url": photo_url,
        }

    except:
        return {
            "name": None,
            "address": None,
            "rating": None,
            "user_ratings_total": None,
            "photo_url": None,
        }


# ---------------------------------------------------------
# FETCH REVIEWS
# ---------------------------------------------------------
def get_place_reviews(place_id: str, max_reviews: int = 5):
    try:
        params = {
            "place_id": place_id,
            "fields": "reviews",
            "key": PLACES_KEY,
        }
        resp = requests.get(DETAILS_URL, params=params, timeout=20)
        data = resp.json()

        reviews = data.get("result", {}).get("reviews", [])
        return [r.get("text", "") for r in reviews if r.get("text")][:max_reviews]

    except:
        return []


# ---------------------------------------------------------
# FETCH PHOTO URL
# ---------------------------------------------------------
def get_place_photo_url(place_id: str, max_width: int = 800):
    try:
        params = {
            "place_id": place_id,
            "fields": "photos",
            "key": PLACES_KEY,
        }
        resp = requests.get(DETAILS_URL, params=params, timeout=20)
        data = resp.json()

        photos = data.get("result", {}).get("photos", [])
        if not photos:
            return None

        ref = photos[0].get("photo_reference")
        if not ref:
            return None

        return (
            f"https://maps.googleapis.com/maps/api/place/photo"
            f"?maxwidth={max_width}&photo_reference={ref}&key={PLACES_KEY}"
        )

    except:
        return None


# ---------------------------------------------------------
# SENTIMENT ANALYSIS WITH DISTILBERT
# ---------------------------------------------------------
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english",
)


def analyze_reviews(reviews):
    results = []
    for text in reviews:
        try:
            out = sentiment_pipeline(text[:512])[0]
            results.append({
                "text": text,
                "label": out["label"],
                "score": float(round(out["score"], 3)),
            })
        except:
            continue
    return results


# ---------------------------------------------------------
# KEYWORD EXTRACTION
# ---------------------------------------------------------
def extract_keywords(texts, max_keywords=5):
    if not texts:
        return []
    try:
        v = CountVectorizer(stop_words="english", max_features=50)
        X = v.fit_transform(texts)
        counts = X.toarray().sum(axis=0)
        vocab = v.get_feature_names_out()
        idx = counts.argsort()[::-1][:max_keywords]
        return [vocab[i] for i in idx]
    except:
        return []


# ---------------------------------------------------------
# SUMMARY NUMBERS
# ---------------------------------------------------------
def summarize_sentiment(results):
    if not results:
        return {
            "avg_score": 0.0,
            "positive_ratio": 0.0,
            "keywords": [],
            "summary": "No reviews available.",
        }

    pos = [r["score"] for r in results if r["label"] == "POSITIVE"]
    neg = [r["score"] for r in results if r["label"] == "NEGATIVE"]

    all_scores = pos + [-s for s in neg]
    avg = np.mean(all_scores)
    pos_ratio = len(pos) / len(results)

    summary = (
        f"{pos_ratio * 100:.1f}% of reviews are positive "
        f"with an average score of {avg:+.2f}."
    )

    return {
        "avg_score": float(round(avg, 2)),
        "positive_ratio": float(round(pos_ratio * 100, 1)),
        "keywords": extract_keywords([r["text"] for r in results]),
        "summary": summary,
    }


# ---------------------------------------------------------
# GEMINI LLM SUMMARY
# ---------------------------------------------------------
def summarize_with_gemini(place_name, sentiment_data, reviews):
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        reviews_text = "\n".join([r["text"] for r in reviews[:5]]) or "No reviews."

        prompt = f"""
Write a short 1–2 sentence human-like summary for {place_name}.

Sentiment Stats:
- {sentiment_data["summary"]}
- Keywords: {', '.join(sentiment_data["keywords"])}

Reviews:
{reviews_text}
"""

        resp = model.generate_content(prompt)
        return resp.text.strip()

    except:
        return "Visitors had mixed experiences."


# ---------------------------------------------------------
# DB HELPERS (SAVE + LOAD)
# ---------------------------------------------------------
def save_reviews_to_db(place_id: str, reviews: list):
    db = SessionLocal()
    try:
        # Remove old reviews
        db.query(SentimentReview).filter(
            SentimentReview.place_id == place_id
        ).delete()

        # Insert new reviews
        for r in reviews:
            db.add(
                SentimentReview(
                    place_id=place_id,
                    text=r["text"],
                    label=r["label"],
                    score=float(r["score"]),
                )
            )

        db.commit()
    finally:
        db.close()


def load_reviews_from_db(place_id: str):
    db = SessionLocal()
    try:
        rows = (
            db.query(SentimentReview)
            .filter(SentimentReview.place_id == place_id)
            .limit(5)
            .all()
        )
        return [
            {"text": r.text, "label": r.label, "score": r.score}
            for r in rows
        ]
    finally:
        db.close()


# ---------------------------------------------------------
# MAIN: SENTIMENT INSIGHTS
# ---------------------------------------------------------
def get_sentiment_insights(place_id: str, place_name: str | None = None):
    db: Session = SessionLocal()

    try:
        # -------------------------
        # 1) Try cached summary
        # -------------------------
        cached = db.query(SentimentCache).filter_by(place_id=place_id).first()

        if cached:
            samples = load_reviews_from_db(place_id)

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
                "samples": samples,
                "last_updated": (
                    cached.last_updated.isoformat()
                    if cached.last_updated else None
                ),
            }

        # -------------------------
        # 2) Not cached → compute fresh
        # -------------------------
        if not place_name:
            place_name = get_place_name(place_id)

        reviews = get_place_reviews(place_id)
        analyzed = analyze_reviews(reviews)
        summary = summarize_sentiment(analyzed)

        gemini_summary = summarize_with_gemini(
            place_name or "this place", summary, analyzed
        )

        photo_url = get_place_photo_url(place_id)

        # -------------------------
        # 3) SAVE cache summary
        # -------------------------
        cache = SentimentCache(
            place_id=place_id,
            place_name=place_name,
            avg_score=summary["avg_score"],
            positive_ratio=summary["positive_ratio"],
            keywords=summary["keywords"],
            summary=summary["summary"],
            human_summary=gemini_summary,
            num_reviews=len(reviews),
            photo_url=photo_url,
        )

        db.add(cache)
        db.commit()

        # -------------------------
        # 4) SAVE raw review samples
        # -------------------------
        save_reviews_to_db(place_id, analyzed[:5])

        # -------------------------
        # 5) Return final structure
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
            "samples": analyzed[:5],   # matches DB
        }

    finally:
        db.close()
