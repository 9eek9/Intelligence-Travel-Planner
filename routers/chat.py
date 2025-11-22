# routers/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from models.schemas import (
    LanguageBuddyRequest, LanguageBuddyResponse
)
from services.chat_service import handle_chatbot
from services.language_service import handle_language, list_supported_languages

router = APIRouter()


# New schema for chat history
class ChatMessage(BaseModel):
    role: str     # "user" or "assistant"
    text: str

class ChatHistoryRequest(BaseModel):
    history: List[ChatMessage] = []
    message: str


@router.post("/bot")
async def chatbot(req: ChatHistoryRequest):
    """
    Multi-turn chatbot endpoint.
    Frontend sends previous messages + latest message.
    """
    try:
        reply = await handle_chatbot(
            history=[{"role": m.role, "text": m.text} for m in req.history],
            new_message=req.message
        )
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Language Buddy remains unchanged
@router.post("/language", response_model=LanguageBuddyResponse)
def language_buddy(req: LanguageBuddyRequest):
    try:
        reply = handle_language(
            text=req.message,
            mode=req.mode,
            source_lang=req.source_lang,
            target_lang=req.target_lang,
            tone=req.tone,
        )
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
def get_supported_languages():
    return {"supported_languages": list_supported_languages()}
