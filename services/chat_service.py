import os
from google import genai
from typing import List, Dict

# Use same model as gemini_service
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


async def handle_chatbot(history: List[Dict], new_message: str) -> str:
    """
    Multi-turn chatbot (Frontend-only history).
    - history: list of {"role": "user"/"assistant", "text": "..."}
    - new_message: latest user message
    """

    conversation = []

    # Include past conversation
    for msg in history:
        if msg["role"] == "user":
            conversation.append({
                "role": "user",
                "parts": [{"text": msg["text"]}]
            })
        else:
            conversation.append({
                "role": "model",
                "parts": [{"text": msg["text"]}]
            })

    # Add latest user message
    conversation.append({
        "role": "user",
        "parts": [{"text": new_message}]
    })

    # Call Gemini 2.5 Flash
    response = client.models.generate_content(
        model=MODEL,
        contents=conversation
    )

    # Extract text safely
    if hasattr(response, "text"):
        return response.text

    return response.candidates[0].content.parts[0].text
