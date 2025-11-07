# routers/chat.py
from fastapi import APIRouter, HTTPException
from models.schemas import (
    ChatbotRequest, ChatbotResponse,
    LanguageBuddyRequest, LanguageBuddyResponse
)
from services.chat_service import handle_chatbot
from services.language_service import handle_language, list_supported_languages

router = APIRouter()

@router.post("/bot", response_model=ChatbotResponse)
def chatbot(req: ChatbotRequest):
    try:
        reply = handle_chatbot(req.message)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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