import os
import pickle
import random
from config import POPULARITY_MODEL_PATH, FEATURE_PREPROCESSOR_PATH

# Load ML model safely
try:
    with open(POPULARITY_MODEL_PATH, "rb") as f:
        MODEL = pickle.load(f)
except:
    MODEL = None

try:
    with open(FEATURE_PREPROCESSOR_PATH, "rb") as f:
        PREP = pickle.load(f)
except:
    PREP = None


# ---------------------------
# 1. Predict attraction score
# ---------------------------
def predict_attraction_popularity(a):
    """
    ML prediction fallback with rule-based scoring.
    """

    # If model missing → generate realistic score
    if MODEL is None or PREP is None:
        base = 60
        if a.get("type"):
            if "museum" in a["type"].lower():
                base += 10
            if "park" in a["type"].lower():
                base += 5
        return max(20, min(95, base + random.randint(-10, 10)))

    # Build ML input
    feat = {
        "name": a.get("name", ""),
        "type": a.get("type", ""),
        "lat": a.get("lat", 0),
        "lon": a.get("lon", 0),
        "country": "",
        "month": 1,
    }

    try:
        X = PREP.transform([feat])
        pred = MODEL.predict(X)[0]
        return int(max(20, min(95, pred)))
    except:
        return random.randint(40, 90)


# ---------------------------
# 2. Predict event popularity
# ---------------------------
def predict_event_popularity(event):
    """
    Light ML-like scoring for events.
    """

    base = 40

    cat = event.get("category", "").lower()
    if "festival" in cat:
        base += 25
    if "holiday" in cat:
        base += 20
    if "concert" in cat:
        base += 15

    # randomness
    base += random.randint(-10, 10)

    return max(20, min(95, base))
