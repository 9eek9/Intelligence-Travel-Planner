import os, json
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional

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


# === Chatbot + Language Buddy (BEGIN) === #
_GEMINI_INITIALIZED = False
_MODEL = None

def _init():
    global _GEMINI_INITIALIZED, _MODEL
    if _GEMINI_INITIALIZED:
        return
    api_key = os.getenv("GEMINI_API_KEY")
    # use same model as itinerary
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    genai.configure(api_key=api_key)
    _MODEL = genai.GenerativeModel(model_name)
    _GEMINI_INITIALIZED = True

def generate_text(prompt: str, system: Optional[str] = None) -> str:
    """Simple text generation wrapper for MVP."""
    _init()
    if system:
        full = f"{system}\n\nUser: {prompt}"
    else:
        full = prompt
    resp = _MODEL.generate_content(full)
    return getattr(resp, "text", "").strip()

def chat_translate(text: str, target_lang: str = "en", tone: str = "polite") -> str:
    system = (
        "You are Language Buddy for Smart Travel. Keep outputs concise and natural."
        " Preserve meaning. Use the requested tone."
    )
    prompt = f"Translate to {target_lang} with {tone} tone:\n{text}"
    return generate_text(prompt, system=system)

def chat_correct(text: str, lang: str = "en") -> str:
    system = (
        "You are a gentle language corrector. Fix grammar and wording while keeping meaning."
        " After the corrected sentence, give 1-2 short bullet explanations."
    )
    prompt = f"Correct this {lang} sentence:\n{text}\nReturn: corrected sentence then 1-2 bullets."
    return generate_text(prompt, system=system)

def chat_explain(text: str, lang: str = "en") -> str:
    system = "You are a concise language tutor. Explain briefly with one or two examples."
    prompt = f"Explain the grammar/wording issues in this {lang} text and how to improve:\n{text}"
    return generate_text(prompt, system=system)

def chat_travel_answer(message: str) -> str:
    system = (
        "You are Smart Travel's Chat Assistant. Be concise, friendly, budget-aware."
        " If suggesting places, keep lists short (3-5). Avoid inventing exact prices."
    )
    return generate_text(message, system=system)


# === Chatbot + Language Buddy (END) === #