from fastapi import APIRouter
import httpx
import os
import traceback

router = APIRouter()

@router.get("/debug/unsplash")
async def debug_unsplash(query: str = "Toronto"):
    try:
        key = os.getenv("UNSPLASH_KEY")
        if not key:
            return {"error": "UNSPLASH_KEY is missing in environment variables"}

        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {key}"}

        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, params={"query": query, "per_page": 1}, headers=headers)

        return {
            "status": r.status_code,
            "response": r.text,
        }
    except Exception as e:
        return {
            "error": str(e),
            "trace": traceback.format_exc(),
        }
