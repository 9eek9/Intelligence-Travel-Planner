# services/chat_service.py
from .gemini_service import chat_travel_answer

def handle_chatbot(message: str) -> str:
    return chat_travel_answer(message)
