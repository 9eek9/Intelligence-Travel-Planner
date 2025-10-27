# services/sentiment_service.py
import os, requests, numpy as np
from dotenv import load_dotenv
from transformers import pipeline
from sklearn.feature_extraction.text import CountVectorizer
from services.gemini_service import generate_itinerary_text
import google.generativeai as genai


load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
genai.configure(api_key=GEMINI_KEY)

PLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# Initialize DistilBERT model (cached)
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)


# ----------- Fetch Google Reviews -----------
def get_place_reviews(place_id: str, max_reviews: int = 5):
    """Fetch up to 5 latest reviews for a given Google place."""
    try:
        params = {"place_id": place_id, "fields": "reviews", "key": PLACES_KEY}
        resp = requests.get(DETAILS_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        reviews = data.get("result", {}).get("reviews", [])
        return [r.get("text", "") for r in reviews if r.get("text")]
    except Exception:
        return []


# ----------- Analyze Sentiment Using DistilBERT -----------
def analyze_reviews(reviews):
    results = []
    for text in reviews:
        try:
            out = sentiment_pipeline(text[:512])[0]  # Truncate long reviews
            results.append({
                "text": text,
                "label": out["label"],
                "score": round(out["score"], 3)
            })
        except Exception:
            continue
    return results


# ----------- Extract Frequent Keywords -----------
def extract_keywords(texts, max_keywords=5):
    if not texts:
        return []
    try:
        vectorizer = CountVectorizer(stop_words="english", max_features=50)
        X = vectorizer.fit_transform(texts)
        counts = X.toarray().sum(axis=0)
        vocab = vectorizer.get_feature_names_out()
        top_indices = counts.argsort()[::-1][:max_keywords]
        return [vocab[i] for i in top_indices]
    except Exception:
        return []


# ----------- Aggregate Review Sentiment -----------
def summarize_sentiment(results):
    if not results:
        return {
            "avg_score": 0,
            "positive_ratio": 0,
            "keywords": [],
            "summary": "No reviews available."
        }

    pos = [r["score"] for r in results if r["label"] == "POSITIVE"]
    neg = [r["score"] for r in results if r["label"] == "NEGATIVE"]

    avg_score = np.mean(pos + [-s for s in neg]) if results else 0
    positive_ratio = len(pos) / len(results)
    texts = [r["text"] for r in results]
    keywords = extract_keywords(texts)

    summary = f"{positive_ratio*100:.1f}% of reviews are positive with an average score of {avg_score:+.2f}."

    return {
        "avg_score": round(avg_score, 2),
        "positive_ratio": round(positive_ratio*100, 1),
        "keywords": keywords,
        "summary": summary
    }


# ----------- Summarize with Gemini -----------
def summarize_with_gemini(place_name: str, sentiment_data: dict, reviews: list):
    """
    Use Gemini to convert numeric sentiment data + example reviews into a human summary.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        reviews_text = "\n".join([r["text"] for r in reviews[:5]]) or "No reviews found."
        prompt = f"""
You are an AI travel assistant. Based on the following Google reviews for {place_name},
write ONE short, human-like summary (max 2 sentences) describing the general sentiment.

Sentiment Statistics:
- {sentiment_data["summary"]}
- Positive ratio: {sentiment_data["positive_ratio"]}%
- Keywords: {', '.join(sentiment_data['keywords'])}

Reviews:
{reviews_text}

Example response format:
"Most travelers enjoyed the skyline views but mentioned long wait times."

Now write your summary:
"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "Visitors generally had mixed experiences."



# ----------- Main Entry Point -----------
def get_sentiment_insights(place_id: str, place_name: str = None):
    reviews = get_place_reviews(place_id)
    analyzed = analyze_reviews(reviews)
    summary = summarize_sentiment(analyzed)

    # Gemini-powered human summary
    gemini_summary = summarize_with_gemini(place_name or "this place", summary, analyzed)

    return {
        "place_id": place_id,
        "num_reviews": len(reviews),
        "summary": summary["summary"],
        "avg_score": summary["avg_score"],
        "positive_ratio": summary["positive_ratio"],
        "keywords": summary["keywords"],
        "human_summary": gemini_summary, 
        "samples": analyzed[:3] # first 3 reviews
    }

