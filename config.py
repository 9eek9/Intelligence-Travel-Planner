import os
from dotenv import load_dotenv

# Load .env
load_dotenv() 
OPENTRIP_API_KEY = os.getenv("OPENTRIP_API_KEY")
CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_KEY")
PREDICTHQ_TOKEN = os.getenv("PREDICTHQ_KEY")
UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")

print("DEBUG OPENTRIP_API_KEY =", OPENTRIP_API_KEY)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ML model paths
POPULARITY_MODEL_PATH = "popularity_model.pkl"         # attractions model
FEATURE_PREPROCESSOR_PATH = "feature_preprocessor.pkl"
SEASONALITY_MODEL_PATH = "seasonal_popularity.joblib"  # optional
