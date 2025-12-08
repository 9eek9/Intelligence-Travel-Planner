from fastapi import APIRouter
from services.seasonal_service import get_seasonal_suggestions

router = APIRouter(prefix="/seasonal", tags=["Seasonal Suggestions"])

@router.get("/suggestions")
async def seasonal_suggestions(to: str, start: str, end: str):
    """
    Handles seasonal suggestions (async).
    """
    result = await get_seasonal_suggestions(to, start, end)
    return result
