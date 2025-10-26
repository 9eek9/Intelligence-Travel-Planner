import os, json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

BUDGET_DESC = {
    0: "free or extremely low cost options only (parks, free museums, scenic walks)",
    1: "inexpensive options such as casual dining, cheap attractions, public transport",
    2: "moderately priced options such as mid-range restaurants and affordable activities",
    3: "expensive options including fine dining, premium attractions, private tours",
    4: "luxury options including Michelin-starred restaurants, exclusive experiences, and luxury transport"
}


def generate_itinerary_text(destination: str,
                            days: int,
                            budget: int,
                            kid_friendly: bool,
                            plan_struct: list,
                            travel_type: str = None,
                            activity_theme: str = None):
    model = genai.GenerativeModel(MODEL)
    budget_text = BUDGET_DESC.get(budget, "moderately priced options")

    prompt = f"""
You are a professional travel planner. Create a {days}-day itinerary for {destination}.

Constraints:
- Budget level: {budget} → {budget_text}.
- Kid friendly: {kid_friendly}.
- Travel type: {travel_type or 'unspecified'}.
- Activity theme: {activity_theme or 'general interest'}.
- Organize each day into Morning / Afternoon / Evening.
- Mention prices appropriately (affordable, luxury, free entry).
- Include one restaurant recommendation per day.
- Keep descriptions natural, concise, and engaging.
- Use ONLY the provided JSON data — do not invent extra places.

POI Data (JSON):
{json.dumps(plan_struct, indent=2)}
"""

    response = model.generate_content(prompt)
    return response.text
